"""APK Pure Downloader Class."""

from typing import Any, Self

from src.app import APP
from src.downloader.download import Downloader


class ApkPure(Downloader):
    """Files downloader."""

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download whatever the latest version of app from apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        file_name = f"{app.app_name}.apk"
        self._download(app.download_source, file_name)
        return file_name, app.download_source
