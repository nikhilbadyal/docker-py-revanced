"""Google Drive downloader Class."""

from typing import Any, Self

import gdown

from src.app import APP
from src.downloader.download import Downloader


class GoogleDrive(Downloader):
    """Google Driver downloader."""

    def specific_version(self: Self, app: APP, version: str) -> tuple[str, str]:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        return self.latest_version(app)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download whatever the latest version of app from Google Driver.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        url = app.download_source
        file_name = f"{self.config.temp_folder_name}/{app.app_name}.apk"
        _, download_url = gdown.download(url, quiet=False, use_cookies=False, output=file_name)
        return file_name, download_url
