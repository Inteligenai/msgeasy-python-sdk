"""
Keeps each method's parameters level with the request shape it builds.

The parameters are written out by hand, so they are the one thing here that can
fall behind the contract: a field added to a request schema reaches the generated
model on the next regeneration, and a caller cannot pass it until someone adds it
to the signature too. Nothing breaks, which is what makes it easy to miss — so it
fails here instead.

Spelling the parameters out is deliberate. Forwarding `**fields` straight to the
model would never drift, but pydantic ignores what it does not recognise, so
`send(txt="hi")` would send a message with no text and no complaint.
"""

from __future__ import annotations

import inspect
import unittest
from typing import Any, Callable, List, Set, Tuple, Type

from pydantic import BaseModel

from msgeasy._generated.models.check_verification_input import CheckVerificationInput
from msgeasy._generated.models.create_template_input import CreateTemplateInput
from msgeasy._generated.models.send_message_input import SendMessageInput
from msgeasy._generated.models.start_verification_input import StartVerificationInput
from msgeasy._generated.models.update_template_input import UpdateTemplateInput
from msgeasy.resources.messages import MessagesResource
from msgeasy.resources.templates import TemplatesResource
from msgeasy.resources.verify import VerifyResource

#: On every method, and never part of a request body.
CONTROL = {"self", "timeout", "idempotency_key"}

#: Method, the shape it builds, and any parameter that is not a body field.
BODIES: List[Tuple[Callable[..., Any], Type[BaseModel], Set[str]]] = [
    (VerifyResource.start, StartVerificationInput, set()),
    (VerifyResource.check, CheckVerificationInput, set()),
    (MessagesResource.send, SendMessageInput, set()),
    (TemplatesResource.create, CreateTemplateInput, set()),
    (TemplatesResource.validate, CreateTemplateInput, set()),
    (TemplatesResource.update, UpdateTemplateInput, {"template_id"}),
]


class SignatureTest(unittest.TestCase):
    def test_every_request_field_is_reachable(self) -> None:
        for method, model, path_params in BODIES:
            with self.subTest(method=method.__qualname__):
                self.assertEqual(parameters(method, path_params), fields(model))


def parameters(method: Callable[..., Any], path_params: Set[str]) -> Set[str]:
    return set(inspect.signature(method).parameters) - CONTROL - path_params


def fields(model: Type[BaseModel]) -> Set[str]:
    return set(model.model_fields)


if __name__ == "__main__":
    unittest.main()
