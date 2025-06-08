import logging
from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from collections import defaultdict, deque

class RequestLoggingMiddleware:
    """
    Middleware to log user requests including timestamp, user, and request path.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            file_handler = logging.FileHandler('requests.log')
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.email if hasattr(request.user, 'email') else str(request.user)
        else:
            user = "Anonymous"
        
        self.logger.info(
            f"{datetime.now()} - User: {user} - Path: {request.path}"
        )
        
        response = self.get_response(request)
        
        return response

class RestrictAccessByTimeMiddleware:
    """
    Custom middleware to restrict access to the application based on time.
    Access is allowed only between 9 PM (21:00) and 6 AM (06:00).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_hour = datetime.now().hour
        
        if current_hour >= 21 or current_hour < 6:
            return self.get_response(request)
        else:
            return self._deny_access()

    def _deny_access(self):
        """
        Return a 403 Forbidden response when access is denied.
        """
        return Response(
            "Access is restricted to (9 PM - 6 AM).",
            status=status.HTTP_403_FORBIDDEN
        )

class OffensiveLanguageMiddleware:
    """
    Middleware to limit POST requests (messages) per IP address.
    Allows maximum 5 messages per minute per IP address.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.ip_message_tracker = defaultdict(deque)
        self.message_limit = 5 
        self.time_window = datetime.timedelta(minutes=1) 

    def __call__(self, request):
        if request.method == 'POST':
            client_ip = self._get_client_ip(request)
            
            if self._is_rate_limited(client_ip):
                return self._deny_access()
        
        response = self.get_response(request)
        return response

    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _is_rate_limited(self, ip_address):
        """
        Check if the IP address has exceeded the rate limit.
        Returns True if rate limited, False otherwise.
        """
        current_time = datetime.now()
        ip_timestamps = self.ip_message_tracker[ip_address]
        
        while ip_timestamps and current_time - ip_timestamps[0] > self.time_window:
            ip_timestamps.popleft()
        
        if len(ip_timestamps) >= self.message_limit:
            return True
        
        ip_timestamps.append(current_time)
        return False

    def _deny_access(self):
        """
        Return a 429 Too Many Requests response when rate limited.
        """
        return Response(
            {
                "error": "Rate limit exceeded",
                "message": f"Maximum {self.message_limit} messages per minute allowed",
                "retry_after": "60 seconds"
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

class RolepermissionMiddleware:
    """
    Middleware to check if the user has the required role for the request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            user_role = getattr(user, 'role', None)  
            
            if user_role not in ['admin', 'moderator']:
                return Response(
                    {"error": "You do not have permission to perform this action."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        response = self.get_response(request)
        return response