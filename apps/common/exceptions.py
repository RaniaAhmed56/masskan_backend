"""Project-wide DRF exception handler.

Wraps DRF's default handler so every error response — validation errors,
403s, 404s, throttling, uncaught 500s — comes back in one consistent
envelope instead of each view inventing its own error shape:

    {
        "error": {
            "code": "validation_error",
            "message": "Human readable summary.",
            "details": { ...original DRF error data... }
        }
    }

Frontend code can therefore always read `error.message` for a toast and
`error.details` when it needs field-level messages, regardless of which
endpoint failed.
"""

from rest_framework.views import exception_handler as drf_exception_handler


def _summarize(details):
    if isinstance(details, dict):
        for value in details.values():
            summary = _summarize(value)
            if summary:
                return summary
    if isinstance(details, list) and details:
        return str(details[0])
    if isinstance(details, str):
        return details
    return None


def masskan_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", exc.__class__.__name__.lower())
    message = _summarize(response.data) or "Something went wrong."

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": response.data,
        }
    }
    return response
