import uuid
import logging

# It's good practice to get a logger instance if the middleware itself needs to log
# For example, if there was an issue generating a request_id, though unlikely here.
# middleware_logger = logging.getLogger(__name__)


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # Generate a unique request ID
        request.request_id = str(uuid.uuid4())

        # If you want to log the request_id being set (optional, can be verbose)
        # middleware_logger.debug(f"Request ID {request.request_id} generated for path {request.path}",
        # extra={'request_id': request.request_id})

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
