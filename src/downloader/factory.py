"""Downloader Factory."""

from src.config import RevancedConfig
from src.downloader.apkmirror import ApkMirror
from src.downloader.apkmonk import ApkMonk
from src.downloader.apkpure import ApkPure
from src.downloader.apksos import ApkSos
from src.downloader.download import Downloader
from src.downloader.github import Github
from src.downloader.google_drive import GoogleDrive
from src.downloader.sources import (
    APK_MIRROR_BASE_URL,
    APK_MONK_BASE_URL,
    APK_PURE_BASE_URL,
    APKS_SOS_BASE_URL,
    DRIVE_DOWNLOAD_BASE_URL,
    GITHUB_BASE_URL,
    UPTODOWN_SUFFIX,
)
from src.downloader.uptodown import UptoDown
from src.exceptions import DownloadError


class DownloaderFactory(object):
    """Downloader Factory."""

    @staticmethod
    def create_downloader(config: RevancedConfig, apk_source: str) -> Downloader:
        """Returns appropriate downloader.

        Args:
        ----
            config : Config
            apk_source : Source URL for APK
        """
        if apk_source.startswith(GITHUB_BASE_URL):
            return Github(config)
        if apk_source.startswith(APK_PURE_BASE_URL):
            return ApkPure(config)
        if apk_source.startswith(APKS_SOS_BASE_URL):
            return ApkSos(config)
        if apk_source.endswith(UPTODOWN_SUFFIX):
            return UptoDown(config)
        if apk_source.startswith(APK_MIRROR_BASE_URL):
            return ApkMirror(config)
        if apk_source.startswith(APK_MONK_BASE_URL):
            return ApkMonk(config)
        if apk_source.startswith(DRIVE_DOWNLOAD_BASE_URL):
            return GoogleDrive(config)
        msg = "No download factory found."
        raise DownloadError(msg, url=apk_source)
