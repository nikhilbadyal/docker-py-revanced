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
from src.utils import (
    check_java,
    delete_old_changelog,
    generate_obtainium_export,
    load_older_updates,
    save_patch_info,
    write_changelog_to_file,
)

# Shared cache tuple keeps app-processing helpers explicit without repeating the full nested type.
AppCaches = tuple[
    dict[tuple[str, str], tuple[str, str]],
    dict[str, tuple[str, str]],
    Lock,
    Lock,
]


def get_app(config: RevancedConfig, app_name: str) -> APP:
    """Get App object."""
    env_package_name = config.env.str(f"{app_name}_PACKAGE_NAME".upper(), None)
    package_name = env_package_name or Patches.get_package_name(app_name)
    return APP(app_name=app_name, package_name=package_name, config=config)


def process_single_app(
    app_name: str,
    config: RevancedConfig,
    caches: AppCaches,
) -> dict[str, Any]:
    """Process a single app and return its update info."""
    download_cache, resource_cache, download_lock, resource_lock = caches
    logger.info(f"Trying to build {app_name}")
    try:
        app = get_app(config, app_name)

        # Resource downloads use shared in-run caches unless the operator disables caching in config.
        app.download_patch_resources(config, resource_cache, resource_lock)

        patcher = Patches(config, app)
        parser = Parser(patcher, config)
        app_all_patches = patcher.get_app_configs(app)

        # APK downloads use shared in-run caches unless the operator disables caching in config.
        app.download_apk_for_patching(config, download_cache, download_lock)

        parser.include_exclude_patch(app, app_all_patches, patcher.patches_dict)
        logger.info(app)
        app_update_info = save_patch_info(app, {})
        parser.patch_app(app)
    except AppNotFoundError as e:
        logger.info(e)
        raise
    except PatchesJsonLoadError:
        logger.exception("Patches.json not found")
        raise
    except PatchingFailedError as e:
        logger.exception(e)
        raise
    except BuilderError as e:
        logger.exception(f"Failed to build {app_name} because of {e}")
        raise
    else:
        logger.info(f"Successfully completed {app_name}")
        return app_update_info


def _build_caches() -> AppCaches:
    """Create cache containers and locks shared across app workers."""
    # Cache policy is enforced by callers, but the tuple shape stays stable for app-processing helpers.
    return {}, {}, Lock(), Lock()


def _record_failed_app(app_name: str, error: Exception, failed_apps: list[str]) -> None:
    """Log and remember a failed app without hiding it from the final build result."""
    logger.exception(f"Error processing {app_name}: {error}")
    logger.info(f"{app_name} - FAILED")
    # The build continues collecting independent successes before deciding whether anything usable was produced.
    failed_apps.append(app_name)


def _process_apps_sequentially(
    config: RevancedConfig,
    caches: AppCaches,
    updates_info: dict[str, Any],
    failed_apps: list[str],
) -> None:
    """Process apps one-by-one for single-app and CI-test runs."""
    for app_name in config.apps:
        try:
            app_updates = process_single_app(app_name, config, caches)
            updates_info.update(app_updates)
        except Exception as e:  # noqa: BLE001
            _record_failed_app(app_name, e, failed_apps)


def _process_apps_in_parallel(
    config: RevancedConfig,
    caches: AppCaches,
    updates_info: dict[str, Any],
    failed_apps: list[str],
) -> None:
    """Process apps with worker concurrency while preserving aggregate failure reporting."""
    # Worker count is capped by app count and operator config so a large env file does not overload the runner.
    max_workers = min(len(config.apps), config.max_parallel_apps)
    logger.info(f"Processing {len(config.apps)} apps in parallel with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submitting everything first lets independent apps finish even if one app fails early.
        future_to_app = {}
        for app_name in config.apps:
            future = executor.submit(process_single_app, app_name, config, caches)
            future_to_app[future] = app_name
        total_apps = len(config.apps)

        for completed_count, future in enumerate(as_completed(future_to_app), 1):
            app_name = future_to_app[future]
            try:
                app_updates = future.result()
                updates_info.update(app_updates)
                logger.info(f"Progress: {completed_count}/{total_apps} apps completed ({app_name})")
            except Exception as e:  # noqa: BLE001
                logger.info(f"Progress: {completed_count}/{total_apps} apps completed ({app_name} - FAILED)")
                _record_failed_app(app_name, e, failed_apps)


def _raise_if_no_apps_succeeded(failed_apps: list[str], updates_info: dict[str, Any]) -> None:
    """Fail only when the builder produced no patched app metadata at all."""
    if not failed_apps:
        return

    msg = f"Failed to build {len(failed_apps)} app(s): {', '.join(sorted(failed_apps))}"
    if updates_info:
        # Partial builds are still useful release inputs; patch-specific app failures should stay visible as warnings.
        logger.warning(f"{msg}. Continuing because {len(updates_info)} app(s) completed successfully.")
        return

    # No successful app means the build produced nothing usable, so callers should receive a failed process.
    raise PatchingFailedError(msg)


def main() -> None:
    """Entry point."""
    env = Env()
    env.read_env()
    config = RevancedConfig(env)
    updates_info = {}
    failed_apps: list[str] = []
    Downloader.extra_downloads(config)
    if not config.dry_run:
        check_java()
        delete_old_changelog()
        updates_info = load_older_updates(env)

    logger.info(f"Will Patch only {len(config.apps)} apps-:\n{config.apps}")

    if config.disable_caching:
        # The cache containers still satisfy helper signatures, but callers skip reading or populating them.
        logger.info("Download and resource caches are disabled for this run.")

    caches = _build_caches()

    try:
        if len(config.apps) == 1 or config.ci_test:
            _process_apps_sequentially(config, caches, updates_info, failed_apps)
        else:
            _process_apps_in_parallel(config, caches, updates_info, failed_apps)
    finally:
        # Always write partial metadata for successful apps before surfacing the aggregate failure.
        write_changelog_to_file(updates_info)
        generate_obtainium_export(updates_info, config)

    _raise_if_no_apps_succeeded(failed_apps, updates_info)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(1)
