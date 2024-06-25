"""Github Manager."""

import json
import os
import urllib.request
from pathlib import Path
from typing import Self

from environs import Env

from src.app import APP
from src.manager.release_manager import ReleaseManager
from src.utils import app_dump_key, branch_name, updates_file, updates_file_url


class GitHubManager(ReleaseManager):
    """Release manager with GitHub."""

    def __init__(self: Self, env: Env) -> None:
        self.update_file_url = updates_file_url.format(
            github_repository=env.str("GITHUB_REPOSITORY"),
            branch_name=branch_name,
            updates_file=updates_file,
        )

    def get_last_version(self: Self, app: APP, resource_name: str) -> str:
        """Get last patched version."""
        if os.getenv("DRY_RUN", default=None):
            with Path(updates_file).open() as url:
                data = json.load(url)
        else:
            with urllib.request.urlopen(self.update_file_url) as url:
                data = json.load(url)
        if data.get(app.app_name):
            return str(data[app.app_name][resource_name])
        return "0"

    def get_last_version_source(self: Self, app: APP, resource_name: str) -> str:
        """Get last patched version."""
        if os.getenv("DRY_RUN", default=None):
            with Path(updates_file).open() as url:
                data = json.load(url)
        else:
            with urllib.request.urlopen(self.update_file_url) as url:
                data = json.load(url)
        if data.get(app.app_name):
            return str(data[app.app_name][app_dump_key][resource_name])
        return "0"
