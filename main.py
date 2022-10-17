"""Entry point."""
import sys

from environs import Env
from loguru import logger

from src.config import RevancedConfig
from src.downloader import Downloader
from src.parser import Parser
from src.patches import Patches


def main() -> None:
    """Entry point."""
    env = Env()
    config = RevancedConfig(env)

    patcher = Patches(config)
    downloader = Downloader(config)
    parser = Parser(patcher, config)

    logger.info(f"Will Patch only {patcher.config.apps}")
    for app in patcher.config.apps:
        try:
            logger.info("Trying to build %s" % app)
            app_all_patches, version, is_experimental = patcher.get_app_configs(app)
            version = downloader.download_apk_to_patch(version, app)
            patcher.include_exclude_patch(app, parser, app_all_patches)
            logger.info(f"Downloaded {app}, version {version}")
            parser.patch_app(app=app, version=version, is_experimental=is_experimental)
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")
    if config.build_og_nd_branding_youtube:
        logger.info("Rebuilding youtube")
        all_patches = parser.get_all_patches()
        branding_index = all_patches.index(config.branding_patch)
        was_og_build = True if all_patches[branding_index - 1] == "-e" else False
        output = "-custom-icon-" if was_og_build else "-original-icon-"
        app = "youtube"
        _, version, is_experimental = patcher.get_app_configs(app)
        parser.invert_patch(config.branding_patch)
        parser.patch_app(
            app=app,
            version=version,
            is_experimental=is_experimental,
            output_prefix=output,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(-1)
