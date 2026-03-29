class SecurityHeadersMiddleware:
    """Add security headers to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response["X-Content-Type-Options"] = "nosniff"
        if not response.has_header("X-Frame-Options"):
            response["X-Frame-Options"] = "SAMEORIGIN"
        return response
