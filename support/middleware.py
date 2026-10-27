import time
import logging

logger = logging.getLogger('fitora.requests')

class RequestLoggingMiddleware:
    """
    Logs incoming HTTP requests and response performance metrics.
    Ensures no passwords, session cookies, or API keys are logged.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        
        # Process request
        response = self.get_response(request)
        
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        user_info = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'Anonymous'
        
        logger.info(
            f"METHOD={request.method} PATH={request.path} STATUS={response.status_code} "
            f"DURATION={duration_ms}ms USER={user_info} IP={self._get_client_ip(request)}"
        )
        return response

    def process_exception(self, request, exception):
        logger.error(
            f"Unhandled exception on PATH={request.path} METHOD={request.method}: {str(exception)}",
            exc_info=True
        )
        return None

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '-')
