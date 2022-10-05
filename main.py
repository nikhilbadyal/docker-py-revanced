import sys

from environs import Env
from loguru import logger

from src.downloader import Downloader
from src.parser import Parser
from src.patches import Patches


def main() -> None:
    env = Env()

    patcher = Patches(env)
    downloader = Downloader(env)
    parser = Parser(patcher, env)

    logger.info(f"Will Patch only {patcher.apps}")
    for app in patcher.apps:
        try:
            logger.info("Trying to build %s" % app)
            app_all_patches, version, is_experimental = patcher.get_app_configs(app)
            version = downloader.download_apk_to_patch(version, app, patcher)
            patcher.include_and_exclude_patches(app, parser, app_all_patches)
            logger.info(f"Downloaded {app}, version {version}")
            parser.patch_app(app=app, version=version, is_experimental=is_experimental)
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(-1)
