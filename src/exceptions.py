"""Possible Exceptions."""
from typing import Any, Self


class APKMirrorIconScrapError(Exception):
    """Exception raised when the icon cannot be scraped from apkmirror."""

    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        """Initialize the APKMirrorIconScrapFailure exception.

        Args:
        ----
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                url (str, optional): The URL of the failed icon scraping. Defaults to None.
        """
        super().__init__(*args)
        self.url = kwargs.get("url", None)


class APKComboIconScrapError(APKMirrorIconScrapError):
    """Exception raised when the icon cannot be scraped from apkcombo."""


class DownloadError(Exception):
    """Generic Download failure."""

    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        """Initialize the APKMirrorAPKDownloadFailure exception.

        Args:
        ----
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                url (str, optional): The URL of the failed icon scraping. Defaults to None.
        """
        super().__init__(*args)
        self.url = kwargs.get("url", None)


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


class PatchingFailedError(Exception):
    """Patching Failed."""


class AppNotFoundError(ValueError):
    """Not a valid Revanced App."""


class PatchesJsonLoadError(ValueError):
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
        self.file_name = kwargs.get("file_name", None)


class UnknownError(Exception):
    """Some unknown error."""
