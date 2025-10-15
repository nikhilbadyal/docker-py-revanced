"""Entry point."""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Any

from environs import Env
from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.downloader.download import Downloader
from src.exceptions import AppNotFoundError, BuilderError, PatchesJsonLoadError, PatchingFailedError
from src.parser import Parser
from src.patches import Patches
from src.utils import check_java, delete_old_changelog, load_older_updates, save_patch_info, write_changelog_to_file


def get_app(config: RevancedConfig, app_name: str) -> APP:
    """Get App object."""
    env_package_name = config.env.str(f"{app_name}_PACKAGE_NAME".upper(), None)
    package_name = env_package_name or Patches.get_package_name(app_name)
    return APP(app_name=app_name, package_name=package_name, config=config)


def process_single_app(
    app_name: str,
    config: RevancedConfig,
    caches: tuple[
        dict[tuple[str, str], tuple[str, str]],
        dict[str, tuple[str, str]],
        Lock,
        Lock,
    ],
) -> dict[str, Any]:
    """Process a single app and return its update info."""
    download_cache, resource_cache, download_lock, resource_lock = caches
    logger.info(f"Trying to build {app_name}")
    try:
        app = get_app(config, app_name)

        # Use shared resource cache with thread safety
        app.download_patch_resources(config, resource_cache, resource_lock)

        patcher = Patches(config, app)
        parser = Parser(patcher, config)
        app_all_patches = patcher.get_app_configs(app)

        # Use shared APK cache with thread safety
        app.download_apk_for_patching(config, download_cache, download_lock)

        parser.include_exclude_patch(app, app_all_patches, patcher.patches_dict)
        logger.info(app)
        app_update_info = save_patch_info(app, {})
        parser.patch_app(app)
    except AppNotFoundError as e:
        logger.info(e)
        return {}
    except PatchesJsonLoadError:
        logger.exception("Patches.json not found")
        return {}
    except PatchingFailedError as e:
        logger.exception(e)
        return {}
    except BuilderError as e:
        logger.exception(f"Failed to build {app_name} because of {e}")
        return {}
    else:
        logger.info(f"Successfully completed {app_name}")
        return app_update_info


def main() -> None:
    """Entry point."""
    env = Env()
    env.read_env()
    config = RevancedConfig(env)
    updates_info = {}
    Downloader.extra_downloads(config)
    if not config.dry_run:
        check_java()
        delete_old_changelog()
        updates_info = load_older_updates(env)

    logger.info(f"Will Patch only {len(config.apps)} apps-:\n{config.apps}")

    # Shared caches for reuse across all apps (empty if caching disabled)
    download_cache: dict[tuple[str, str], tuple[str, str]] = {}
    resource_cache: dict[str, tuple[str, str]] = {}

    # Thread-safe locks for cache access
    download_lock = Lock()
    resource_lock = Lock()

    # Clear caches if caching is disabled
    if config.disable_caching:
        download_cache.clear()
        resource_cache.clear()

    # Determine optimal number of workers (don't exceed number of apps or CPU cores)
    max_workers = min(len(config.apps), config.max_parallel_apps)

    if len(config.apps) == 1 or config.ci_test:
        # For single app or CI testing, use sequential processing
        caches = (download_cache, resource_cache, download_lock, resource_lock)
        for app_name in config.apps:
            app_updates = process_single_app(app_name, config, caches)
            updates_info.update(app_updates)
    else:
        # For multiple apps, use parallel processing
        logger.info(f"Processing {len(config.apps)} apps in parallel with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all app processing tasks
            caches = (download_cache, resource_cache, download_lock, resource_lock)
            future_to_app = {
                executor.submit(process_single_app, app_name, config, caches): app_name for app_name in config.apps
            }

            # Collect results as they complete
            total_apps = len(config.apps)

            for completed_count, future in enumerate(as_completed(future_to_app), 1):
                app_name = future_to_app[future]
                try:
                    app_updates = future.result()
                    updates_info.update(app_updates)
                    logger.info(f"Progress: {completed_count}/{total_apps} apps completed ({app_name})")
                except BuilderError as e:
                    logger.exception(f"Error processing {app_name}: {e}")
                    logger.info(f"Progress: {completed_count}/{total_apps} apps completed ({app_name} - FAILED)")

    write_changelog_to_file(updates_info)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(1)
