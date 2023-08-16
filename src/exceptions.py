from typing import Any


class APKMirrorIconScrapFailure(Exception):
    """Exception raised when the icon cannot be scraped from apkmirror."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the APKMirrorIconScrapFailure exception.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                url (str, optional): The URL of the failed icon scraping. Defaults to None.
        """
        super().__init__(*args)
        self.url = kwargs.get("url", None)


class PatchingFailed(Exception):
    """Patching Failed."""

    pass


class AppNotFound(ValueError):
    """Not a valid Revanced App."""

    pass


class PatchesJsonFailed(ValueError):
    """Patches failed."""

    pass
