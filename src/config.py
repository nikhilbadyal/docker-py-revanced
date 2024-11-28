"""Revanced Configurations."""

from pathlib import Path
from typing import Self

from environs import Env

from src.utils import default_build, default_cli, default_patches, default_patches_json, resource_folder


class RevancedConfig(object):
    """Revanced Configurations."""

    def __init__(self: Self, env: Env) -> None:
        self.env = env
        self.temp_folder_name = resource_folder
        self.temp_folder = Path(self.temp_folder_name)
        self.ci_test = env.bool("CI_TEST", False)
        self.rip_libs_apps: list[str] = []
        self.existing_downloaded_apks = env.list("EXISTING_DOWNLOADED_APKS", [])
        self.personal_access_token = env.str("PERSONAL_ACCESS_TOKEN", None)
        self.dry_run = env.bool("DRY_RUN", False)
        self.global_cli_dl = env.str("GLOBAL_CLI_DL", default_cli)
        self.global_patches_dl = env.str("GLOBAL_PATCHES_DL", default_patches)
        self.global_patches_json_dl = env.str("GLOBAL_PATCHES_JSON_DL", default_patches_json)
        self.global_keystore_name = env.str("GLOBAL_KEYSTORE_FILE_NAME", "revanced.keystore")
        self.global_options_file = env.str("GLOBAL_OPTIONS_FILE", "options.json")
        self.global_archs_to_build = env.list("GLOBAL_ARCHS_TO_BUILD", [])
        self.extra_download_files: list[str] = env.list("EXTRA_FILES", [])
        self.apk_editor = "apkeditor-output.jar"
        self.extra_download_files.append("https://github.com/REAndroid/APKEditor@apkeditor.jar")
        self.apps = env.list("PATCH_APPS", default_build)
        self.global_old_key = env.bool("GLOBAL_OLD_KEY", True)
        self.global_space_formatted = env.bool("GLOBAL_SPACE_FORMATTED_PATCHES", True)
