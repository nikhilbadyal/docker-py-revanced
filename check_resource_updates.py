"""Check patching resource updates."""

from environs import Env
from loguru import logger

from main import get_app
from src.config import RevancedConfig
from src.manager.github import GitHubManager
from src.utils import default_build, integration_version_key, integrations_dl_key, patches_dl_key, patches_version_key


def check_if_build_is_required() -> bool:
    """Read resource version."""
    env = Env()
    env.read_env()
    config = RevancedConfig(env)
    needs_to_repatched = []
    for app_name in env.list("PATCH_APPS", default_build):
        logger.info(f"Checking {app_name}")
        app_obj = get_app(config, app_name)
        old_integration_version = GitHubManager(env).get_last_version(app_obj, integration_version_key)
        old_integration_source = GitHubManager(env).get_last_version_source(app_obj, integrations_dl_key)
        old_patches_version = GitHubManager(env).get_last_version(app_obj, patches_version_key)
        old_patches_source = GitHubManager(env).get_last_version_source(app_obj, patches_dl_key)
        app_obj.download_patch_resources(config)
        if GitHubManager(env).should_trigger_build(
            old_integration_version,
            old_integration_source,
            app_obj.resource["integrations"]["version"],
            app_obj.integrations_dl,
        ) or GitHubManager(env).should_trigger_build(
            old_patches_version,
            old_patches_source,
            app_obj.resource["patches"]["version"],
            app_obj.patches_dl,
        ):
            caused_by = {
                "app_name": app_name,
                "integration": {
                    "old": old_integration_version,
                    "new": app_obj.resource["integrations"]["version"],
                },
                "patches": {
                    "old": old_patches_version,
                    "new": app_obj.resource["patches"]["version"],
                },
            }
            logger.info(f"New build can be triggered caused by {caused_by}")
            needs_to_repatched.append(app_name)
    logger.info(f"{needs_to_repatched} are need to repatched.")
    if needs_to_repatched:
        print(",".join(needs_to_repatched))  # noqa: T201
        return True
    return False


check_if_build_is_required()
