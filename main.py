"""Entry point."""
import sys

from environs import Env
from loguru import logger

from src.config import RevancedConfig
from src.exceptions import AppNotFoundError, PatchesJsonLoadError, PatchingFailedError, UnknownError
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
    if not config.dry_run:
        check_java()

    logger.info(f"Will Patch only {config.apps}")
    for possible_app in config.apps:
        logger.info(f"Trying to build {possible_app}")
        try:
            app = APP(app_name=possible_app, config=config)
            patcher = Patches(config, app)
            parser = Parser(patcher, config)
            app_all_patches = patcher.get_app_configs(app)
            app.download_apk_for_patching(config)
            patcher.include_exclude_patch(app, parser, app_all_patches)
            logger.info(app)
            parser.patch_app(app)
        except AppNotFoundError as e:
            logger.info(e)
        except PatchesJsonLoadError:
            logger.exception("Patches.json not found")
        except PatchingFailedError as e:
            logger.exception(e)
        except UnknownError as e:
            logger.exception(f"Failed to build {app} because of {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(1)
