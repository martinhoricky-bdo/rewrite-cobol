from django.http import Http404


class NotFound(Http404):
    """Represent a safe not-found message that may be shown to the user."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
