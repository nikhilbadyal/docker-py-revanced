"""Possible Exceptions."""

from typing import Any, Self


class BuilderError(Exception):
    """Base class for all the project errors."""

    message = "Default Error message."

    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        if args:
            self.message = args[0]
        super().__init__(self.message)

    def __str__(self: Self) -> str:
        """Return error message."""
        return self.message


class ScrapingError(BuilderError):
    """Exception raised when the url cannot be scraped."""

    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        """Initialize the APKMirrorIconScrapFailure exception.

        Args:
        ----
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                url (str, optional): The URL of the failed icon scraping. Defaults to None.
        """
        super().__init__(*args)
        self.url = kwargs.get("url")

    def __str__(self: Self) -> str:
        """Exception message."""
        base_message = super().__str__()
        return f"Message - {base_message} Url - {self.url}"


class APKMirrorIconScrapError(ScrapingError):
    """Exception raised when the icon cannot be scraped from apkmirror."""


class APKComboIconScrapError(ScrapingError):
    """Exception raised when the icon cannot be scraped from apkcombo."""


class APKPureIconScrapError(ScrapingError):
    """Exception raised when the icon cannot be scraped from apkpure."""


class APKMonkIconScrapError(ScrapingError):
    """Exception raised when the icon cannot be scraped from apkmonk."""


class DownloadError(BuilderError):
    """Generic Download failure."""

    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        """Initialize the DownloadFailure exception.

        Args:
        ----
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                url (str, optional): The URL of the failed icon scraping. Defaults to None.
        """
        super().__init__(*args)
        self.url = kwargs.get("url")

    def __str__(self: Self) -> str:
        """Exception message."""
        base_message = super().__str__()
        return f"Message - {base_message} Url - {self.url}"


class APKDownloadError(DownloadError):
    """Exception raised when the apk cannot be scraped."""


class APKMirrorAPKDownloadError(APKDownloadError):
    """Exception raised when downloading an APK from apkmirror failed."""


class APKMonkAPKDownloadError(APKDownloadError):
    """Exception raised when downloading an APK from apkmonk failed."""


class APKMirrorAPKNotFoundError(APKDownloadError):
    """Exception raised when apk doesn't exist on APKMirror."""


class UptoDownAPKDownloadError(APKDownloadError):
    """Exception raised when downloading an APK from uptodown failed."""


class APKPureAPKDownloadError(APKDownloadError):
    """Exception raised when downloading an APK from apkpure failed."""


class APKSosAPKDownloadError(APKDownloadError):
    """Exception raised when downloading an APK from apksos failed."""


class PatchingFailedError(BuilderError):
    """Patching Failed."""


class AppNotFoundError(BuilderError):
    """Not a valid Revanced App."""


class PatchesJsonLoadError(BuilderError):
    """Failed to load patches json."""

    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        """Initialize the PatchesJsonLoadFailed exception.

        Args:
        ----
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                file_name (str, optional): The name of json file. Defaults to None.
        """
        super().__init__(*args)
        self.file_name = kwargs.get("file_name")

    def __str__(self: Self) -> str:
        """Exception message."""
        base_message = super().__str__()
        return f"Message - {base_message} File - {self.file_name}"
