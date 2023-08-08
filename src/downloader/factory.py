"""Downloader Factory."""
from src.config import RevancedConfig
from src.downloader.apkmirror import ApkMirror
from src.downloader.apkpure import ApkPure
from src.downloader.apksos import ApkSos
from src.downloader.download import Downloader
from src.downloader.github import Github
from src.downloader.uptodown import UptoDown
from src.patches import Patches


class DownloaderFactory(object):
    """Downloader Factory."""

    @staticmethod
    def create_downloader(
        app: str, patcher: Patches, config: RevancedConfig
    ) -> Downloader:
        """Returns appropriate downloader.

        Parameters
        ----------
        app : App Name
        patcher : Patcher
        config : Config
        """
        if app in {"patches", "microg"}:
            return Github(patcher, config)
        if app in config.apk_pure:
            return ApkPure(patcher, config)
        elif app in config.apk_sos:
            return ApkSos(patcher, config)
        elif app in config.upto_down:
            return UptoDown(patcher, config)
        else:
            return ApkMirror(patcher, config)
