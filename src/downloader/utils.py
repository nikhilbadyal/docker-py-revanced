"""Utility class."""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from src.config import RevancedConfig
from src.patches import Patches
from src.utils import PatcherDownloadFailed

implement_method = "Please implement the method"


def download_revanced(config: RevancedConfig, patcher: Patches) -> None:
    """Download Revanced and Extended Patches, Integration and CLI."""
    from src.downloader.factory import DownloaderFactory

    if os.path.exists("changelog.md") and not config.dry_run:
        logger.debug("Deleting old changelog.md")
        os.remove("changelog.md")
    assets = [
        ["revanced", "revanced-cli", config.normal_cli_jar],
        ["revanced", "revanced-integrations", config.normal_integrations_apk],
        ["revanced", "revanced-patches", config.normal_patches_jar],
    ]
    if config.build_extended:
        assets += [
            ["inotia00", "revanced-cli", config.cli_jar],
            ["inotia00", "revanced-integrations", config.integrations_apk],
            ["inotia00", "revanced-patches", config.patches_jar],
        ]
    if (
        "youtube" in config.apps
        or "youtube_music" in config.apps
        or "microg" in config.apps
    ):
        if config.build_extended and "microg" in config.apps:
            assets += [
                ["inotia00", "mMicroG", "microg.apk"],
            ]
        else:
            assets += [
                ["inotia00", "mMicroG", "microg-output.apk"],
            ]
    downloader = DownloaderFactory.create_downloader(
        app="patches", patcher=patcher, config=config
    )
    with ThreadPoolExecutor(7) as executor:
        futures = [
            executor.submit(
                downloader.download,
                version="latest",
                app=repo[2],
                **{"owner": repo[0], "name": repo[1]},
            )
            for repo in assets
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                raise PatcherDownloadFailed(f"An exception occurred: {e}")
    logger.info("Downloaded revanced microG ,cli, integrations and patches.")
