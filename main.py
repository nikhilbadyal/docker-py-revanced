"""Entry point."""
import sys

from environs import Env
from loguru import logger

from src.config import RevancedConfig
from src.exceptions import AppNotFound, PatchesJsonLoadFailed, PatchingFailed
from src.parser import Parser
from src.patches import Patches
from src.utils import check_java, extra_downloads


def main() -> None:
    """Entry point."""
    from src.app import APP

    env = Env()
    env.read_env()
    config = RevancedConfig(env)
    extra_downloads(config)
    check_java(config.dry_run)

    logger.info(f"Will Patch only {config.apps}")
    for app in config.apps:
        logger.info(f"Trying to build {app}")
        try:
            app = APP(app_name=app, config=config)
            patcher = Patches(config, app)
            parser = Parser(patcher, config)
            app_all_patches = patcher.get_app_configs(app)
            app.download_apk_for_patching(config)
            patcher.include_exclude_patch(app, parser, app_all_patches)
            logger.info(app)
            parser.patch_app(app)
        except AppNotFound as e:
            logger.info(f"Invalid app requested to build {e}")
        except PatchesJsonLoadFailed:
            logger.exception("Patches.json not found")
        except PatchingFailed as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(1)
