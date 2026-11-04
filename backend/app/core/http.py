import httpx


def describe_error(e: BaseException) -> str:
    """Error text that is safe to log or show: httpx messages include the full URL, and
    Steam Web API URLs carry our API key in the query string."""
    if isinstance(e, httpx.HTTPStatusError):
        url = e.request.url.copy_with(query=None)
        return f"HTTP {e.response.status_code} from {url}"
    if isinstance(e, httpx.HTTPError):
        try:
            return f"{type(e).__name__} calling {e.request.url.copy_with(query=None)}"
        except RuntimeError:  # no request attached
            return type(e).__name__
    return str(e)
