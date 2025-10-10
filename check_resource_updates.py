"""Check patching resource updates."""

from threading import Lock

from environs import Env
from loguru import logger

from main import get_app
from src.config import RevancedConfig
from src.manager.github import GitHubManager
from src.utils import default_build, patches_dl_list_key, patches_versions_key


def check_if_build_is_required() -> bool:
    """Read resource version."""
    env = Env()
    env.read_env()
    config = RevancedConfig(env)
    needs_to_repatched = []
    resource_cache: dict[str, tuple[str, str]] = {}
    resource_lock = Lock()
    for app_name in env.list("PATCH_APPS", default_build):
        logger.info(f"Checking {app_name}")
        app_obj = get_app(config, app_name)
        old_patches_versions = GitHubManager(env).get_last_version(app_obj, patches_versions_key)
        old_patches_sources = GitHubManager(env).get_last_version_source(app_obj, patches_dl_list_key)

        # Backward compatibility for string version/source
        if isinstance(old_patches_versions, str):
            old_patches_versions = [old_patches_versions]
        if isinstance(old_patches_sources, str):
            old_patches_sources = [old_patches_sources]

        app_obj.download_patch_resources(config, resource_cache, resource_lock)

        new_patches_versions = app_obj.get_patch_bundles_versions()
        if len(old_patches_versions) != len(new_patches_versions) or len(old_patches_sources) != len(
            app_obj.patches_dl_list,
        ):
            caused_by = {
                "app_name": app_name,
                "patches": {
                    "old_versions": old_patches_versions,
                    "old_bundles": old_patches_sources,
                    "new_versions": new_patches_versions,
                    "new_bundles": app_obj.patches_dl_list,
                },
            }
            logger.info(
                f"New build can be triggered due to change in number of patch bundles or sources, info: {caused_by}",
            )
            needs_to_repatched.append(app_name)
            continue

        for old_version, old_source, new_version, new_source in zip(
            old_patches_versions,
            old_patches_sources,
            new_patches_versions,
            app_obj.patches_dl_list,
            strict=True,
        ):
            if GitHubManager(env).should_trigger_build(
                old_version,
                old_source,
                new_version,
                new_source,
            ):
                caused_by = {
                    "app_name": app_name,
                    "patches": {
                        "old": old_version,
                        "new": new_version,
                    },
                }
                logger.info(f"New build can be triggered caused by {caused_by}")
                needs_to_repatched.append(app_name)
                break
    logger.info(f"{needs_to_repatched} are need to repatched.")
    if needs_to_repatched:
        print(",".join(needs_to_repatched))  # noqa: T201
        return True
    return False


check_if_build_is_required()
