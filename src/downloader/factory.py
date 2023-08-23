"""Downloader Factory."""
from src.config import RevancedConfig
from src.downloader.apkmirror import ApkMirror
from src.downloader.apkpure import ApkPure
from src.downloader.apksos import ApkSos
from src.downloader.download import Downloader
from src.downloader.github import Github
from src.downloader.sources import (
    APK_MIRROR_BASE_URL,
    APK_PURE_URL,
    APK_SOS_URL,
    GITHUB_BASE_URL,
    apk_sources,
)
from src.downloader.uptodown import UptoDown
from src.exceptions import DownloadFailure


class DownloaderFactory(object):
    """Downloader Factory."""

    @staticmethod
    def create_downloader(app: str, config: RevancedConfig) -> Downloader:
        """Returns appropriate downloader.

        Parameters
        ----------
        app : App Name
        config : Config
        """
        if apk_sources[app].startswith(GITHUB_BASE_URL):
            return Github(config)
        if apk_sources[app].startswith(APK_PURE_URL):
            return ApkPure(config)
        elif apk_sources[app].startswith(APK_SOS_URL):
            return ApkSos(config)
        elif apk_sources[app].endswith("en.uptodown.com/android"):
            return UptoDown(config)
        elif apk_sources[app].startswith(APK_MIRROR_BASE_URL):
            return ApkMirror(config)
        raise DownloadFailure(f"No download factory found for {app}")
