"""APK Pure Downloader Class."""
from typing import Any

from loguru import logger

from src.downloader.download import Downloader
from src.utils import AppNotFound


class ApkPure(Downloader):
    """Files downloader."""

    def latest_version(self, app: str, **kwargs: Any) -> None:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        package_name = None
        for package, app_tuple in self.patcher.revanced_app_ids.items():
            if app_tuple[0] == app:
                package_name = package
        if not package_name:
            logger.info("Unable to download from apkpure")
            raise AppNotFound()
        download_url = f"https://d.apkpure.com/b/APK/{package_name}?version=latest"
        self._download(download_url, f"{app}.apk")
        logger.debug(f"Downloaded {app} apk from apk_pure_downloader in rt")
