"""Downloader Factory."""
from src.config import RevancedConfig
from src.downloader.apkmirror import ApkMirror
from src.downloader.apkpure import ApkPure
from src.downloader.apksos import ApkSos
from src.downloader.download import Downloader
from src.downloader.github import Github
from src.downloader.sources import (
    APK_MIRROR_BASE_URL,
    APK_PURE_BASE_URL,
    APKS_SOS_BASE_URL,
    GITHUB_BASE_URL,
)
from src.downloader.uptodown import UptoDown
from src.exceptions import DownloadFailure


class DownloaderFactory(object):
    """Downloader Factory."""

    @staticmethod
    def create_downloader(config: RevancedConfig, apk_source: str) -> Downloader:
        """Returns appropriate downloader.

        Parameters
        ----------
        app : App Name
        config : Config
        apk_source : Source URL for APK
        """
        if apk_source.startswith(GITHUB_BASE_URL):
            return Github(config)
        if apk_source.startswith(APK_PURE_BASE_URL):
            return ApkPure(config)
        elif apk_source.startswith(APKS_SOS_BASE_URL):
            return ApkSos(config)
        elif apk_source.endswith("en.uptodown.com/android"):
            return UptoDown(config)
        elif apk_source.startswith(APK_MIRROR_BASE_URL):
            return ApkMirror(config)
        raise DownloadFailure("No download factory found.")
