"""APK Pure Downloader Class."""
from typing import Any, Tuple

from src.downloader.download import Downloader
from src.downloader.sources import apk_sources
from src.patches import Patches


class ApkPure(Downloader):
    """Files downloader."""

    def latest_version(self, app: str, **kwargs: Any) -> Tuple[str, str]:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        package_name = Patches.get_package_name(app)
        download_url = apk_sources[app].format(package_name)
        file_name = f"{app}.apk"
        self._download(download_url, file_name)
        return file_name, download_url
