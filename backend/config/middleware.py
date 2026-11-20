from django.utils.cache import patch_cache_control


class PrivateAPIResponseMiddleware:
    """Keeps users' API responses out of shared caches.

    Requests that carry credentials (a bearer token, or the admin's session)
    get `Cache-Control: private` unless the view set its own policy, so
    proxies/CDNs never store one user's data and serve it to someone else.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        has_credentials = (
            bool(request.headers.get("Authorization")) or request.user.is_authenticated
        )
        response = self.get_response(request)
        if has_credentials and not response.has_header("Cache-Control"):
            patch_cache_control(response, private=True)
        return response
