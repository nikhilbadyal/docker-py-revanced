"""APK Pure Downloader Class."""
from typing import Any, Tuple

from src.app import APP
from src.downloader.download import Downloader
from src.patches import Patches


class ApkPure(Downloader):
    """Files downloader."""

    def latest_version(self, app: APP, **kwargs: Any) -> Tuple[str, str]:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        package_name = Patches.get_package_name(app.app_name)
        download_url = app.download_source.format(package_name)
        file_name = f"{app.app_name}.apk"
        self._download(download_url, file_name)
        return file_name, download_url
