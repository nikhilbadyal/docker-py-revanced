"""Entry point."""
import sys

from environs import Env
from loguru import logger

from src.config import RevancedConfig
from src.downloader.factory import DownloaderFactory
from src.parser import Parser
from src.patches import Patches
from src.utils import AppNotFound, PatchesJsonFailed, check_java


def main() -> None:
    """Entry point."""
    from src.app import APP

    env = Env()
    config = RevancedConfig(env)
    check_java(config.dry_run)

    logger.info(f"Will Patch only {config.apps}")
    for app in config.apps:
        logger.info(f"Trying to build {app}")
        try:
            app = APP(app_name=app, config=config)
            patcher = Patches(config, app)
            parser = Parser(patcher, config)
            app_all_patches = patcher.get_app_configs(app)
            patcher.include_exclude_patch(app, parser, app_all_patches)
            downloader = DownloaderFactory.create_downloader(
                app=app.app_name, patcher=patcher, config=config
            )
            downloader.download(app.app_version, app.app_name)
            parser.patch_app(app)
        except AppNotFound as e:
            logger.info(f"Invalid app requested to build {e}")
        except PatchesJsonFailed:
            logger.exception("Patches.json not found")
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(1)
