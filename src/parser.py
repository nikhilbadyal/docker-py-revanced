"""Revanced Parser."""

from pathlib import Path
from subprocess import PIPE, Popen
from time import perf_counter
from typing import Self

from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.exceptions import PatchingFailedError
from src.patches import Patches
from src.utils import possible_archs


class Parser(object):
    """Revanced Parser."""

    CLI_JAR = "-jar"
    APK_ARG = "-a"
    NEW_APK_ARG = "patch"
    PATCHES_ARG = "-b"
    INTEGRATIONS_ARG = "-m"
    OUTPUT_ARG = "-o"
    KEYSTORE_ARG = "--keystore"
    OPTIONS_ARG = "--options"

    def __init__(self: Self, patcher: Patches, config: RevancedConfig) -> None:
        self._PATCHES: list[str] = []
        self._EXCLUDED: list[str] = []
        self.patcher = patcher
        self.config = config

    def include(self: Self, name: str) -> None:
        """The function `include` adds a given patch to a list of patches.

        Parameters
        ----------
        name : str
            The `name` parameter is a string that represents the name of the patch to be included.
        """
        self._PATCHES.extend(["-i", name])

    def exclude(self: Self, name: str) -> None:
        """The `exclude` function adds a given patch to the list of excluded patches.

        Parameters
        ----------
        name : str
            The `name` parameter is a string that represents the name of the patch to be excluded.
        """
        self._PATCHES.extend(["-e", name])
        self._EXCLUDED.append(name)

    def get_excluded_patches(self: Self) -> list[str]:
        """The function `get_excluded_patches` is a getter method that returns a list of excluded patches.

        Returns
        -------
            The method is returning a list of excluded patches.
        """
        return self._EXCLUDED

    def get_all_patches(self: Self) -> list[str]:
        """The function "get_all_patches" is a getter method that returns a ist of all patches.

        Returns
        -------
            The method is returning a list of all patches.
        """
        return self._PATCHES

    def invert_patch(self: Self, name: str) -> bool:
        """The function `invert_patch` takes a name as input, it toggles the status of the patch.

        Parameters
        ----------
        name : str
            The `name` parameter is a string that represents the name of a patch.

        Returns
        -------
            a boolean value. It returns True if the patch name is found in the list of patches and
        successfully inverted, and False if the patch name is not found in the list.
        """
        try:
            name = name.lower().replace(" ", "-")
            patch_index = self._PATCHES.index(name)
            indices = [i for i in range(len(self._PATCHES)) if self._PATCHES[i] == name]
            for patch_index in indices:
                if self._PATCHES[patch_index - 1] == "-e":
                    self._PATCHES[patch_index - 1] = "-i"
                else:
                    self._PATCHES[patch_index - 1] = "-e"
        except ValueError:
            return False
        else:
            return True

    def exclude_all_patches(self: Self) -> None:
        """The function `exclude_all_patches` exclude all the patches."""
        for idx, item in enumerate(self._PATCHES):
            if item == "-i":
                self._PATCHES[idx] = "-e"

    def include_exclude_patch(
        self: Self,
        app: APP,
        patches: list[dict[str, str]],
        patches_dict: dict[str, list[dict[str, str]]],
    ) -> None:
        """The function `include_exclude_patch` includes and excludes patches for a given app."""
        if app.space_formatted:
            for patch in patches:
                normalized_patch = patch["name"].lower().replace(" ", "-")
                (
                    self.include(patch["name"])
                    if normalized_patch not in app.exclude_request
                    else self.exclude(
                        patch["name"],
                    )
                )
            for patch in patches_dict["universal_patch"]:
                normalized_patch = patch["name"].lower().replace(" ", "-")
                self.include(patch["name"]) if normalized_patch in app.include_request else ()
        else:
            for patch in patches:
                (
                    self.include(patch["name"])
                    if patch["name"] not in app.exclude_request
                    else self.exclude(
                        patch["name"],
                    )
                )
            for patch in patches_dict["universal_patch"]:
                self.include(patch["name"]) if patch["name"] in app.include_request else ()

    @staticmethod
    def is_new_cli(cli_path: Path) -> tuple[bool, str]:
        """Check if new cli is being used."""
        process = Popen(["java", "-jar", cli_path, "-V"], stdout=PIPE)
        output = process.stdout
        if not output:
            msg = "Failed to send request for patching."
            raise PatchingFailedError(msg)
        combined_result = "".join(line.decode() for line in output)
        if "v3" in combined_result or "v4" in combined_result:
            logger.debug("New cli")
            return True, combined_result
        logger.debug("Old cli")
        return False, combined_result

    # noinspection IncorrectFormatting
    def patch_app(
        self: Self,
        app: APP,
    ) -> None:
        """The function `patch_app` is used to patch an app using the Revanced CLI tool.

        Parameters
        ----------
        app : APP
            The `app` parameter is an instance of the `APP` class. It represents an application that needs
        to be patched.
        """
        is_new, version = self.is_new_cli(self.config.temp_folder.joinpath(app.resource["cli"]))
        if is_new:
            apk_arg = self.NEW_APK_ARG
            exp = "--force"
        else:
            apk_arg = self.APK_ARG
            exp = "--experimental"
        args = [
            self.CLI_JAR,
            app.resource["cli"],
            apk_arg,
            app.download_file_name,
            self.PATCHES_ARG,
            app.resource["patches"],
            self.INTEGRATIONS_ARG,
            app.resource["integrations"],
            self.OUTPUT_ARG,
            app.get_output_file_name(),
            self.KEYSTORE_ARG,
            app.keystore_name,
            self.OPTIONS_ARG,
            "options.json",
        ]
        if app.experiment:
            logger.debug("Using experimental features")
            args.append(exp)
        args[1::2] = map(self.config.temp_folder.joinpath, args[1::2])
        if app.old_key and "v4" in version:
            # https://github.com/ReVanced/revanced-cli/issues/272#issuecomment-1740587534
            old_key_flags = ["--alias=alias", "--keystore-entry-password=ReVanced", "--keystore-password=ReVanced"]
            args.extend(old_key_flags)
        if self.config.ci_test:
            self.exclude_all_patches()
        if self._PATCHES:
            args.extend(self._PATCHES)
        if app.app_name in self.config.rip_libs_apps:
            excluded = set(possible_archs) - set(app.archs_to_build)
            for arch in excluded:
                args.extend(("--rip-lib", arch))
        start = perf_counter()
        logger.debug(f"Sending request to revanced cli for building with args java {args}")
        process = Popen(["java", *args], stdout=PIPE)
        output = process.stdout
        if not output:
            msg = "Failed to send request for patching."
            raise PatchingFailedError(msg)
        for line in output:
            logger.debug(line.decode(), flush=True, end="")
        process.wait()
        logger.info(f"Patching completed for app {app} in {perf_counter() - start:.2f} seconds.")
