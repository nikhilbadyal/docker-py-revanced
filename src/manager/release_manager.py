"""Base release manager."""

from typing import Self

from loguru import logger
from packaging.version import Version

from src.app import APP


class ReleaseManager(object):
    """Base Release manager."""

    def get_last_version(self: Self, app: APP, resource_name: str) -> str:
        """Get last patched version."""
        raise NotImplementedError

    def should_trigger_build(self: Self, old_version: str, new_version: str) -> bool:
        """Function to check if we should trigger a build."""
        logger.info(f"New version {new_version}, Old version {old_version}")
        return Version(new_version) > Version(old_version)  # type: ignore[no-any-return]
