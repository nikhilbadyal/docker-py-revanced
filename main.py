import sys

from environs import Env
from loguru import logger

from src.downloader import Downloader
from src.parser import ArgParser
from src.patches import Patches

env = Env()


def main() -> None:
    patches = Patches(env)
    downloader = Downloader()
    downloader.download_revanced()

    logger.info(f"Will Patch only {patches.apps}")
    for app in patches.apps:
        try:
            arg_parser = ArgParser(patches)
            logger.debug("Trying to build %s" % app)
            app_patches, version, is_experimental = patches.get_patches_version(app)
            version = downloader.download_apk_to_patch(version, app)
            patches.get_patches(app, arg_parser)
            logger.debug(f"Downloaded {app}, version {version}")
            arg_parser.run(app=app, version=version, is_experimental=is_experimental)
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(-1)
