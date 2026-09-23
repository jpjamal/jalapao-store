from django.core.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_handler
from rest_framework.exceptions import ValidationError as APIValidationError


def exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        exc = APIValidationError(getattr(exc, "message_dict", {"detail": exc.messages}))
    response = drf_handler(exc, context)
    if response is not None:
        response.data = {"errors": response.data}
    return response
