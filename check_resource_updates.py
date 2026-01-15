"""Check patching resource updates."""

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

from environs import Env
from loguru import logger

from main import get_app
from src.config import RevancedConfig
from src.manager.github import GitHubManager
from src.utils import default_build, patches_dl_list_key, patches_versions_key


class BuildReason(Enum):
    """Reasons why a build might be triggered."""

    FRESH_BUILD = "Fresh build (no previous record)"
    VERSION_UPDATE = "Version update"
    SOURCE_CHANGE = "Patch source changed"
    BUNDLE_COUNT_CHANGE = "Number of patch bundles changed"


@dataclass
class AppBuildInfo:
    """Information about why an app needs to be rebuilt."""

    app_name: str
    reason: BuildReason
    old_versions: list[str] = field(default_factory=list)
    new_versions: list[str] = field(default_factory=list)
    old_sources: list[str] = field(default_factory=list)
    new_sources: list[str] = field(default_factory=list)

    def get_summary(self) -> str:
        """Get a human-readable summary of the build reason."""
        if self.reason == BuildReason.FRESH_BUILD:
            versions = ", ".join(self.new_versions) if self.new_versions else "N/A"
            return f"[FRESH] No previous build -> {versions}"

        if self.reason == BuildReason.VERSION_UPDATE:
            changes = []
            for old, new in zip(self.old_versions, self.new_versions, strict=False):
                if old != new:
                    changes.append(f"{old} -> {new}")
            return f"[UPDATE] {', '.join(changes)}"

        if self.reason == BuildReason.SOURCE_CHANGE:
            return "[SOURCE] Patch source URL changed"

        if self.reason == BuildReason.BUNDLE_COUNT_CHANGE:
            return f"[BUNDLES] {len(self.old_versions)} -> {len(self.new_versions)} patch bundles"

        return f"[UNKNOWN] {self.reason.value}"


def _is_fresh_build(old_versions: list[str], old_sources: list[str]) -> bool:
    """Check if this is a fresh build with no previous record."""
    no_versions = not old_versions or all(v in ("0", "", None) for v in old_versions)
    no_sources = not old_sources or all(s in ("0", "", None) for s in old_sources)
    return no_versions or no_sources


def _detect_build_reason(
    old_versions: list[str],
    old_sources: list[str],
    new_versions: list[str],
    new_sources: list[str],
) -> BuildReason | None:
    """Detect the reason why a build should be triggered."""
    # Check for fresh build first
    if _is_fresh_build(old_versions, old_sources):
        return BuildReason.FRESH_BUILD

    # Check for bundle count change
    if len(old_versions) != len(new_versions) or len(old_sources) != len(new_sources):
        return BuildReason.BUNDLE_COUNT_CHANGE

    # Check for version or source changes
    for old_ver, old_src, new_ver, new_src in zip(
        old_versions,
        old_sources,
        new_versions,
        new_sources,
        strict=True,
    ):
        if old_src != new_src:
            return BuildReason.SOURCE_CHANGE
        if old_ver != new_ver:
            return BuildReason.VERSION_UPDATE

    return None


def _print_build_summary(build_infos: list[AppBuildInfo]) -> None:
    """Print a formatted summary of all apps that need rebuilding."""
    if not build_infos:
        logger.info("No apps need to be repatched.")
        return

    # Group by reason
    by_reason: dict[BuildReason, list[AppBuildInfo]] = {}
    for info in build_infos:
        by_reason.setdefault(info.reason, []).append(info)

    logger.info("=" * 60)
    logger.info("BUILD SUMMARY")
    logger.info("=" * 60)

    for reason in BuildReason:
        if reason not in by_reason:
            continue
        apps = by_reason[reason]
        logger.info(f"\n{reason.value} ({len(apps)} apps):")
        logger.info("-" * 40)
        for info in apps:
            logger.info(f"  {info.app_name}: {info.get_summary()}")

    logger.info("\n" + "=" * 60)
    logger.info(f"TOTAL: {len(build_infos)} apps need to be repatched")
    logger.info("=" * 60)


def check_if_build_is_required() -> bool:
    """Read resource version and determine which apps need rebuilding."""
    env = Env()
    env.read_env()
    config = RevancedConfig(env)
    build_infos: list[AppBuildInfo] = []
    resource_cache: dict[str, tuple[str, str]] = {}
    resource_lock = Lock()
    github_manager = GitHubManager(env)

    for app_name in env.list("PATCH_APPS", default_build):
        logger.info(f"Checking {app_name}")
        app_obj = get_app(config, app_name)
        old_patches_versions = github_manager.get_last_version(app_obj, patches_versions_key)
        old_patches_sources = github_manager.get_last_version_source(app_obj, patches_dl_list_key)

        # Backward compatibility for string version/source
        if isinstance(old_patches_versions, str):
            old_patches_versions = [old_patches_versions]
        if isinstance(old_patches_sources, str):
            old_patches_sources = [old_patches_sources]

        app_obj.download_patch_resources(config, resource_cache, resource_lock)

        new_patches_versions = app_obj.get_patch_bundles_versions()
        new_patches_sources = app_obj.patches_dl_list

        # Detect why build is needed
        reason = _detect_build_reason(
            old_patches_versions,
            old_patches_sources,
            new_patches_versions,
            new_patches_sources,
        )

        if reason:
            build_info = AppBuildInfo(
                app_name=app_name,
                reason=reason,
                old_versions=old_patches_versions,
                new_versions=new_patches_versions,
                old_sources=old_patches_sources,
                new_sources=new_patches_sources,
            )
            build_infos.append(build_info)
            logger.debug(f"{app_name} needs rebuild: {reason.value}")

    # Print detailed summary
    _print_build_summary(build_infos)

    if build_infos:
        app_names = [info.app_name for info in build_infos]
        print(",".join(app_names))  # noqa: T201
        return True
    return False


check_if_build_is_required()
