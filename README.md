# msgeasy

The official Python client for the MsgEasy WhatsApp API.

Send WhatsApp OTPs, messages and media from your backend, with retries, idempotency keys and typed
errors handled for you.

---

## Install

```bash
pip install "git+https://github.com/Inteligenai/msgeasy-python-sdk.git@v0.1.0"
```

Pin to a released tag, not a branch — see [Inteligenai/msgeasy-python-sdk](https://github.com/Inteligenai/msgeasy-python-sdk) for the latest.

From a checkout of this repo, install it in editable mode instead:

```bash
pip install -e packages/sdk-python
```

Python 3.10 or newer. Pure Python, so one wheel works on Windows, macOS and Linux.

```python
from msgeasy import MsgEasy
```

---

## Send your first OTP

You need an API key from **Settings → Console** in the dashboard. Use a `msg_test_` key while you
build — it runs the whole flow without sending a real WhatsApp message or charging anything.

```python
import os
from msgeasy import MsgEasy

client = MsgEasy(os.environ["MSGEASY_API_KEY"])

verification = client.verify.start(phone="+919812345678")
# verification_id="vrf_...", status="pending", expires_at=datetime, channel="whatsapp"

result = client.verify.check(
    verification_id=verification.verification_id,
    code="123456",
)
# status="approved"
```

A test key returns the code on the `start` response as `code`, so you can complete the flow without
a phone. A live key never does.

**You do not need an approved template to do this.** That approval is usually the thing you are
waiting on Meta for, and a test key skips it.

---

## Client

```python
client = MsgEasy(
    api_key,
    base_url="https://api.msgeasy.com",   # default
    timeout=30.0,                         # seconds, default
)
```

The key is required and comes first. Everything else is keyword-only and optional.

Build one client and reuse it — that keeps connections pooled. It is safe to share across threads,
except for `client.rate_limit`, which reports whichever response arrived last.

Every method also takes a per-call `timeout` that overrides the client's.

The client is a context manager if you want connections released deterministically:

```python
with MsgEasy(api_key) as client:
    client.messages.send(to="+919812345678", type="text", text="hi")
```

### Seeing what went over the wire

The methods return the parsed body and nothing else. `on_response` is called once per attempt,
successful or not, with everything the return value cannot give you — the request id of a
*successful* call, the idempotency key that was sent, both bodies as they were, and whether a retry
happened at all:

```python
def record(event):
    log.info(
        "msgeasy %s %s -> %s request_id=%s attempt=%s %sms",
        event.method, event.url, event.status,
        event.request_id, event.attempt, event.elapsed_ms,
    )

client = MsgEasy(api_key, on_response=record)
```

| Attribute | |
|---|---|
| `method`, `url` | The request, `/v1` included. |
| `status` | `None` when nothing came back — see `transport_error`. |
| `request_body`, `response_body` | Parsed JSON, or the raw text when it would not parse. A media upload reports the file's name, type and size rather than its bytes. |
| `request_id` | From `X-Request-Id`. The only way to get it on a success. |
| `idempotency_key` | The key actually sent. `None` on reads. |
| `rate_limit`, `retry_after_seconds` | As that response reported them. |
| `elapsed_ms`, `attempt` | `attempt` is 1-based, so a retry is a second event. |
| `transport_error` | Why nothing came back, when nothing did. |

An exception raised by your handler is logged to the `msgeasy` logger and swallowed — a logging hook
must not be able to fail a send.

### Async frameworks

Every method is synchronous. Called inside an `async def`, a method holds the event loop until it
returns, and every other request on that worker waits with it — no error, just slow requests under
load. FastAPI, Starlette and other async frameworks are affected; Flask, Django and scripts are not.

Calling on the loop raises a `RuntimeWarning` pointing at your line, so this shows up the first
time you run it:

```python
@app.post("/auth/send-code")
async def send_code(phone: str):
    client.verify.start(phone=phone)     # RuntimeWarning: blocks the event loop
```

Either drop `async`, and the framework runs the route on a thread for you:

```python
@app.post("/auth/send-code")
def send_code(phone: str):
    client.verify.start(phone=phone)
```

or keep it and move the call off the loop:

```python
from starlette.concurrency import run_in_threadpool

await run_in_threadpool(client.verify.start, phone=phone)
# or, with no Starlette: await asyncio.to_thread(client.verify.start, phone=phone)
```

To silence the warning once you have made a deliberate choice:

```python
warnings.filterwarnings("ignore", message="This client is synchronous", category=RuntimeWarning)
```

---

## Verify

Sends a one-time code over WhatsApp and checks it.

```python
client.verify.start(
    phone="+919812345678",   # E.164, required
    channel="whatsapp",      # optional
    ttl_seconds=300,         # optional — how long the code is valid
    code_length=6,           # optional
)
```

Returns `verification_id`, `status`, `expires_at`, `channel`, and — on a test key — `code` and
`test_mode=True`.

```python
client.verify.check(verification_id=..., code="123456")
```

Returns `status` and, when the code was wrong, `remaining_attempts`.

**A wrong code is not an error.** It comes back as `status="invalid"` with the attempts left, so
only a refusal raises. Statuses are `pending`, `approved`, `invalid`, `expired` and `max_attempts`.

---

## Messages

```python
# Text — only within 24 hours of their last inbound message
client.messages.send(to="+919812345678", type="text", text="Your order has shipped")

# Template — works at any time
client.messages.send(
    to="+919812345678",
    type="template",
    template_id="tpl_...",
    variables={"1": "4821"},
)

# Media — upload first, then send the id
media = client.media.upload("invoice.pdf")
client.messages.send(to="+919812345678", type="media", media_id=media.id, caption="Your invoice")
```

`send` also takes `reply_to` with a message id, to thread a reply.

Returns `id`, `status`, `to`, `type`, `whatsapp_message_id`, `error`, `created_at`, and `test_mode`
on a test key.

**`status` is `accepted`, not `delivered`.** It means we took the message, not that it arrived.
Store `message.id` against your own record — it is how you read the status back and how you match
the webhook later.

```python
client.messages.get(message_id)
```

Statuses move `accepted` → `sent` → `delivered` → `read`, or `failed`.

---

## Media

```python
client.media.upload("invoice.pdf")                    # a path
client.media.upload(data, filename="invoice.pdf")     # bytes
```

Returns `id` (a `med_` id to send with), `filename`, `mime_type`, `size_bytes` and `created_at`.
`mime_type` is what we resolved, not what you declared — so an extension-less upload tells you what
was actually stored.

Bytes need a `filename`, and its **extension** is what names the type — both the SDK and the API
resolve the type from it, so `photo.png` works and a bare `photo` is rejected as an unsupported
type.

Sizes are capped per file kind by WhatsApp, and an oversized file raises `InvalidRequestError` with
`code="media_too_large"` rather than being silently truncated.

---

## Templates

A template is a message format Meta has approved in advance. You need one to message somebody
outside the 24-hour window.

```python
for template in client.templates.list_all():
    print(template.id, template.name, template.status)
```

`list_all` iterates **every** template, following the cursor for you. `list` returns one page as it
came — `data` and `has_more` — for when you want to page yourself:

```python
page = client.templates.list(limit=20)
if page.has_more:
    page = client.templates.list(limit=20, starting_after=page.data[-1].id)
```

Both take `status` and `updated_after` to filter. `limit` sizes a page (1-100) on either, never the
total — the same meaning it has in the TypeScript SDK.

```python
client.templates.get(template_id)
```

```python
from msgeasy import TemplateVariableInput

client.templates.create(
    name="order_shipped",
    category="UTILITY",
    language="en",
    body="Hi {{1}}, your order {{2}} has shipped.",
    variables=[
        TemplateVariableInput(index=1, example_value="Asha"),
        TemplateVariableInput(index=2, example_value="A-1481"),
    ],
    footer="Reply STOP to opt out",
)
```

Creating submits it to Meta in one call — there is no draft state. It returns `status="processing"`;
poll `get` until `approved` or `rejected`, then send with the returned `tpl_` id. A rejected
template carries `rejection_reason`.

```python
client.templates.validate(name=..., category=..., language=..., body=...)
```

Checks the same rules `create` enforces **without submitting it or claiming the name**. Returns
`valid` and any `issues`. Worth calling first: a create permanently claims that name on your
WhatsApp Business Account, and Meta keeps a deleted template's name reserved for about 30 days.

```python
client.templates.update(template_id, body="...", footer="...")
```

Only a template Meta has not frozen can be edited — one never submitted, or one it rejected. An
approved or in-review template raises `TemplateError`.

A media header takes a `med_` id from `media.upload`:

```python
from msgeasy import MediaHeaderInput, TemplateHeaderInput

header = TemplateHeaderInput(
    MediaHeaderInput(type="IMAGE", media_id=media.id)
)
```

---

## Errors

Every failure raises something under `MsgEasyError`. **Branch on `code`, never on the HTTP status**
— two different problems can share a status.

```python
from msgeasy import APIError, QuotaError, WindowExpiredError

try:
    client.messages.send(to=to, type="text", text=text)
except WindowExpiredError:
    send_template_instead()
except QuotaError as error:
    alert_ops(error.code, error.details)
except APIError as error:
    log.error("%s (%s) request_id=%s", error.message, error.code, error.request_id)
```

Every `APIError` carries:

| Attribute | What it is |
|---|---|
| `code` | The machine-readable reason. This is what you branch on. |
| `status` | The HTTP status. |
| `message` | A human-readable explanation. |
| `request_id` | From `X-Request-Id`. **Quote this in any support ticket** — it is the key into our request log. |
| `details` | Extra context, varies by code. |
| `retry_after_seconds` | Whole seconds, when the API told us how long to wait. |
| `rate_limit` | The rate-limit state on that response, or `None`. |
| `body` | The raw response body. |

Three sit beside `APIError` rather than under it. `APIConnectionError` means nothing came back at
all — DNS, a reset connection, a timeout. `BadEnvelopeError` means something answered that was not
us, usually a proxy's error page; it carries `status` and `body` and deliberately **no `code`**, so
a caller branching on one is never handed an absence where a code belongs. `ValidationError` means
we refused before sending anything; it is also a `ValueError`, which is what a Python caller expects
from a bad argument. `except MsgEasyError` catches all four.

The classes group codes by **what you can do about them**, so `except QuotaError` is a shortcut and
`error.code` is the full story:

| Class | Codes |
|---|---|
| `AuthenticationError` | `invalid_api_key` |
| `PermissionDeniedError` | `insufficient_scope` |
| `RateLimitError` | `rate_limited` |
| `QuotaError` | `quota_exceeded`, `key_limit_reached`, `spend_cap_reached` |
| `SetupRequiredError` | `verify_not_configured`, `no_sender`, `whatsapp_not_connected` |
| `NotFoundError` | `not_found` |
| `InvalidRequestError` | `invalid_request`, `unsupported_media_type`, `media_too_large` |
| `IdempotencyError` | `idempotency_conflict` |
| `WindowExpiredError` | `window_expired` |
| `TemplateError` | `template_not_approved`, `template_name_taken`, `template_not_editable`, `template_category_not_allowed` |
| `MetaError` | `meta_error` |
| `ServiceUnavailableError` | `service_unavailable` |
| `TestKeyError` | `test_key_not_allowed` |

`APIConnectionError` is raised when there was no response at all — DNS, a reset connection, a
timeout. It carries no `status` or `code`, because nothing was received.

**A code this version has never seen still arrives normally**, as the base `APIError` with `code`
intact. So a refusal the API adds after your release surfaces rather than crashing.

### The codes you will actually hit

| Code | Status | What to do |
|---|---|---|
| `invalid_api_key` | 401 | The key is wrong, expired or revoked. |
| `insufficient_scope` | 403 | Valid key, but it lacks permission for this call. |
| `rate_limited` | 429 | Too fast. **The SDK retries this for you.** |
| `key_limit_reached` | 403 | This key is out of monthly allowance. Raise the key's limit; waiting will not help. |
| `quota_exceeded` | 403 | Your plan is out of allowance. Upgrade or free something up. |
| `spend_cap_reached` | 403 | The key hit its own spend ceiling for the cycle. |
| `window_expired` | 409 | Outside the 24-hour window. Send a template. |
| `template_not_approved` | 409 | Meta has not approved that template yet. |
| `no_sender` | 409 | No active sending number. Fix it in the console. |
| `verify_not_configured` | 409 | No Verify template or sender set up yet. |
| `idempotency_conflict` | 409 | The same key was reused for a different body, or the first request is still running. |
| `not_found` | 404 | The id does not exist, or is not yours. |
| `invalid_request` | 400 | The request is malformed; `message` says how. |
| `media_too_large` | 400 | Over WhatsApp's size limit for that file type. |
| `unsupported_media_type` | 400 | WhatsApp will not carry that file type. |
| `test_key_not_allowed` | 403 | That write reaches Meta, so a test key cannot do it. |
| `meta_error` | 502 | Meta rejected the operation; `details` has their code and trace id. |
| `service_unavailable` | 503 | Briefly unavailable. **The SDK retries this for you.** |
| `whatsapp_not_connected` | 400 | This account has no WhatsApp connection. Connect it in the dashboard; retrying will not help. |
| `template_name_taken` | 409 | That name is already claimed in your WhatsApp account. Meta reserves a deleted name for about 30 days. |
| `template_not_editable` | 409 | Only a never-submitted or rejected template can be edited. Approved and in-review ones are frozen by Meta. |
| `template_category_not_allowed` | 409 | The template is `MARKETING`, which cannot be sent from `/v1`. |

Bad input raises before any request goes out: a malformed phone number is a `pydantic.ValidationError`
from the request model, not a round trip and a `400`.

---

## Retries

Three attempts total, with 0.5s then 1s backoff. When the API sends a `Retry-After`, that wins.

**Retried:** `rate_limited`, `service_unavailable`, network faults, and an `idempotency_conflict`
where the first request is still in flight.

**Not retried:** anything you have to fix yourself — a bad request, a missing scope, an exhausted
quota. And never `meta_error` on a write: Meta may already have taken the message, so retrying could
send it twice.

By the time an exception reaches you, the SDK has already retried anything worth retrying.

---

## Idempotency

Every write gets an `Idempotency-Key` automatically, and **the same key is reused across retries of
that call**. If a retry lands after the original succeeded, the API replays the first result instead
of sending a second message.

You do not have to do anything for this — within one call.

Across calls is different. Our key protects the retries inside a single `send`; it is gone the
moment that call returns. If your process can die between sending and recording the result, hold
your own key and pass it, so the retry replays the first send rather than sending a second message:

```python
key = uuid4().hex
db.record_pending(key=key, to=to)
client.messages.send(to=to, type="text", text=text, idempotency_key=key)
```

Available on every write. Max 255 characters, and not empty — either raises `ValidationError`
before the request goes out, rather than quietly sending without one.

`media.upload` is included: the file itself is part of the fingerprint, so a retried upload replays
the first result rather than storing a second copy.

---

## Rate limits

When your key has a per-minute limit, the API returns its state on every response and the SDK
records it:

```python
list(client.templates.list_all())
client.rate_limit    # RateLimit(limit=100, remaining=99, reset_seconds=1)
```

`client.rate_limit` is `None` on a key with no limit set, and until the first response reports one —
so `None` means *unknown*, never *nothing left*. Absent or complete, never partly filled in, because
the API sends the three headers together or not at all. It is also on any `APIError`, so you can see
the state at the moment you were refused.

It is whatever the most recent response reported, whichever call that was — a pacing signal, not a
per-call fact. With several calls in flight, read `rate_limit` off the `on_response` event instead.

---

## Webhooks

We POST events to your endpoint and sign every delivery. Verify the signature before trusting it.

```python
from msgeasy import verify_webhook_signature
```

**Pass the raw body**, not a parsed-and-re-serialised object. Re-serialising changes the bytes and
the signature will not match. Every framework hides the raw body somewhere different, and this is
the single most common reason a webhook integration fails:

```python
# FastAPI — await the body, and do not declare a Pydantic model parameter
@app.post("/webhooks/msgeasy")
async def webhook(request: Request):
    raw = await request.body()
    result = verify_webhook_signature(raw, request.headers, SECRET)
    if not result:
        log.warning("refused a delivery: %s", result.reason)
        raise HTTPException(status_code=400)
    event = json.loads(raw)
    return {"ok": True}
```

Django (`request.body`, never `request.POST`) and Flask (`request.get_data()`, never
`request.get_json()`) each hide it somewhere else again — the
[webhooks guide](https://msgeasy.com/docs/guides/handle-webhooks) has a working handler for every
framework, and the dedupe and ordering rules besides.

`verify_webhook_signature` takes `str` or `bytes` and never raises. **Pass the whole headers
mapping**, not the extracted value — the lookup is case-insensitive and we do it for you.

It returns a `SignatureResult`, falsy when refused, so `if not result:` reads as before. A header
that arrived twice — as a list value or comma-joined into one string — is refused as
`malformed_header` rather than raising.
`result.reason` says which: `no_secret_configured`, `missing_header`, `malformed_header`,
`stale_timestamp` or `bad_signature` — worth logging, since a clock-skew problem and a wrong secret
need different fixes. **Answer a refusal with a 4xx and process nothing.**

The signature covers a timestamp, so a captured delivery cannot be replayed later. Anything older
than 5 minutes is rejected; pass `tolerance_seconds` to widen that.

Events: `message.sent`, `message.delivered`, `message.read`, `message.failed`, `inbound.received`,
`verify.approved`, `verify.delivered`, `verify.failed`, `template.status_changed`,
`usage.threshold`.

Register your endpoint in the console — there is no API for it.

---

## Test mode

A `msg_test_` key runs the same code as a live key, with several things skipped.

| | Test key | Live key |
|---|---|---|
| Verify needs an approved template | no | yes |
| Sends reach WhatsApp | no | yes |
| The 24-hour window applies | no | yes |
| Counts against your message quota | no | yes |
| Stores a contact | no | yes |
| Returns the OTP code in the response | yes | no |
| Can create templates | no | yes |
| Media upload really uploads | yes | yes |

Responses carry `test_mode=True`. Going live is swapping the key — no code changes.

---

## Type hints

The package ships `py.typed`, so your editor and `mypy` see every field. Request and response types
are generated from the API's own OpenAPI document, so they cannot drift from the live API.

```python
from msgeasy import Message, Template, Verification
```

You rarely name them — you get them back from a call. The four `CreateTemplateInput*` types are the
only ones you construct yourself, and only for the template methods.

---

## Development

```bash
pip install -e ".[dev]"
python -m unittest discover -s tests -t .    # the conformance suite
mypy msgeasy tests
ruff check msgeasy tests
```

To regenerate the core from the OpenAPI document — needs a JVM:

```bash
pnpm --filter @msgeasy/api generate:sdk-python
```

`msgeasy/_generated/` is generated output — never edit it, since the next regeneration overwrites
it. Nothing runs that for you, so after the document changes, regenerate and read `git diff` to see
whether the core moved. Everything else in the package is hand-written and survives a regeneration:
`client.py`, `_transport.py`, `_policy.py`, `errors.py`, `webhooks.py` and `resources/`.
