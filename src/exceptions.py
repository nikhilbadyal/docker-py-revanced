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


class DownloadFailure(Exception):
    """Generic Download failure."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the APKMirrorAPKDownloadFailure exception.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                url (str, optional): The URL of the failed icon scraping. Defaults to None.
        """
        super().__init__(*args)
        self.url = kwargs.get("url", None)


class APKDownloadFailure(DownloadFailure):
    """Exception raised when the apk cannot be scraped."""

    pass


class APKMirrorAPKDownloadFailure(APKDownloadFailure):
    """Exception raised when downloading an APK from apkmirror failed."""

    pass


class APKMirrorAPKNotFound(APKDownloadFailure):
    """Exception raised when apk doesn't exist on APKMirror."""

    pass


class UptoDownAPKDownloadFailure(APKDownloadFailure):
    """Exception raised when downloading an APK from uptodown failed."""

    pass


class APKPureAPKDownloadFailure(APKDownloadFailure):
    """Exception raised when downloading an APK from apkpure failed."""

    pass


class APKSosAPKDownloadFailure(APKDownloadFailure):
    """Exception raised when downloading an APK from apksos failed."""

    pass


class PatchingFailed(Exception):
    """Patching Failed."""

    pass


class AppNotFound(ValueError):
    """Not a valid Revanced App."""

    pass


class PatchesJsonLoadFailed(ValueError):
    """Failed to load patches json."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the PatchesJsonLoadFailed exception.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                file_name (str, optional): The name of json file. Defaults to None.
        """
        super().__init__(*args)
        self.file_name = kwargs.get("file_name", None)
