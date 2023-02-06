"""Entry point."""
import sys

from environs import Env
from loguru import logger

from src.config import RevancedConfig
from src.downloader import Downloader
from src.parser import Parser
from src.patches import Patches
from src.utils import AppNotFound


def main() -> None:
    """Entry point."""
    env = Env()
    config = RevancedConfig(env)

    patcher = Patches(config)
    downloader = Downloader(patcher, config)
    parser = Parser(patcher, config)

    logger.info(f"Will Patch only {patcher.config.apps}")
    for app in patcher.config.apps:
        try:
            logger.info("Trying to build %s" % app)
            app_all_patches, version, is_experimental = patcher.get_app_configs(app)
            version = downloader.download_apk_to_patch(version, app)
            config.app_versions[app] = version
            patcher.include_exclude_patch(app, parser, app_all_patches)
            logger.info(f"Downloaded {app}, version {version}")
            parser.patch_app(app=app, version=version, is_experimental=is_experimental)
        except AppNotFound as e:
            logger.info(f"Invalid app requested to build {e}")
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")
    if len(config.alternative_youtube_patches) and "youtube" in config.apps:
        for alternative_patch in config.alternative_youtube_patches:
            _, version, is_experimental = patcher.get_app_configs("youtube")
            was_inverted = parser.invert_patch(alternative_patch)
            if was_inverted:
                logger.info(
                    f"Rebuilding youtube with inverted {alternative_patch} patch."
                )
                parser.patch_app(
                    app="youtube",
                    version=config.app_versions.get("youtube", "latest"),
                    is_experimental=is_experimental,
                    output_prefix="-" + alternative_patch + "-",
                )
            else:
                logger.info(
                    f"Skipping Rebuilding youtube as {alternative_patch} patch was not found."
                )
    if len(config.alternative_youtube_music_patches) and "youtube_music" in config.apps:
        for alternative_patch in config.alternative_youtube_music_patches:
            _, version, is_experimental = patcher.get_app_configs("youtube_music")
            was_inverted = parser.invert_patch(alternative_patch)
            if was_inverted:
                logger.info(
                    f"Rebuilding youtube music with inverted {alternative_patch} patch."
                )
                parser.patch_app(
                    app="youtube_music",
                    version=config.app_versions.get("youtube_music", "latest"),
                    is_experimental=is_experimental,
                    output_prefix="-" + alternative_patch + "-",
                )
            else:
                logger.info(
                    f"Skipping Rebuilding youtube music as {alternative_patch} patch was not found."
                )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(1)
