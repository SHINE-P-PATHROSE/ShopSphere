"""
Core Exception Handlers - Custom DRF exception handling.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Custom exception handler that returns consistent error responses."""
    response = exception_handler(exc, context)

    if response is not None:
        custom_response = {
            'success': False,
            'error': {
                'status_code': response.status_code,
                'message': _get_error_message(response),
                'details': response.data,
            }
        }
        response.data = custom_response

    return response


def _get_error_message(response):
    """Extract a human-readable error message."""
    status_messages = {
        400: 'Bad Request',
        401: 'Authentication Required',
        403: 'Permission Denied',
        404: 'Not Found',
        405: 'Method Not Allowed',
        429: 'Too Many Requests',
        500: 'Internal Server Error',
    }
    return status_messages.get(response.status_code, 'An error occurred')
