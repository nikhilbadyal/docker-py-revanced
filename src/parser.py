"""Revanced Parser."""

import json
from subprocess import PIPE, Popen
from time import perf_counter
from typing import Any, Self

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
    PATCHES_ARG = "-p"
    OUTPUT_ARG = "-o"
    KEYSTORE_ARG = "--keystore"
    OPTIONS_ARG = "-O"

    def __init__(self: Self, patcher: Patches, config: RevancedConfig) -> None:
        self._PATCHES: list[str] = []
        self._EXCLUDED: list[str] = []
        self.patcher = patcher
        self.config = config

    def format_option(self: Self, opt: dict[str, Any]) -> str:
        """
        The function `include` adds a given patch to the front of a list of patches.

        Parameters
        ----------
        opt : dict[str, Any]
            The `opt` parameter is a dictionary that represents the key-value pair of options
            of the patch to be included.
        """
        pair: str = opt["key"]
        if value := opt.get("value"):
            if isinstance(value, bool):
                pair += f'="{str(value).lower()}"'
            elif isinstance(value, (int, float)):
                pair += f"={value}"  # Numbers should not be quoted
            elif isinstance(value, list):
                formatted_list = ",".join(map(str, value))
                pair += f'="[ {formatted_list} ]"'  # Preserve list format
            else:
                pair += f'="{value}"'
        return pair

    def include(self: Self, name: str, options_list: list[dict[str, Any]]) -> None:
        """
        The function `include` adds a given patch to the front of a list of patches.

        Parameters
        ----------
        name : str
            The `name` parameter is a string that represents the name of the patch to be included.
        options_list : list[dict[str, Any]]
            Then `options_list` parameter is a list of dictionary that represents the options for all patches.
        """
        options_dict: dict[str, Any] = self.fetch_patch_options(name, options_list)
        options = options_dict.get("options", [])
        if options:
            for opt in options:
                pair = self.format_option(opt)
                self._PATCHES[:0] = [self.OPTIONS_ARG, pair]
        self._PATCHES[:0] = ["-e", name]

    def exclude(self: Self, name: str) -> None:
        """The `exclude` function adds a given patch to the list of excluded patches.

        Parameters
        ----------
        name : str
            The `name` parameter is a string that represents the name of the patch to be excluded.
        """
        self._PATCHES.extend(["-d", name])
        self._EXCLUDED.append(name)

    def get_excluded_patches(self: Self) -> list[str]:
        """The function `get_excluded_patches` is a getter method that returns a list of excluded patches.

        Returns
        -------
            The method is returning a list of excluded patches.
        """
        return self._EXCLUDED

    def get_all_patches(self: Self) -> list[str]:
        """The function "get_all_patches" is a getter method that returns the list of all patches.

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
            indices = [i for i in range(len(self._PATCHES)) if self._PATCHES[i] == name]
            for patch_index in indices:
                if self._PATCHES[patch_index - 1] == "-e":
                    self._PATCHES[patch_index - 1] = "-d"
                else:
                    self._PATCHES[patch_index - 1] = "-e"
        except ValueError:
            return False
        else:
            return True

    def exclude_all_patches(self: Self) -> None:
        """The function `exclude_all_patches` exclude all the patches."""
        for idx, item in enumerate(self._PATCHES):
            if idx == 0:
                continue
            if item == "-e":
                self._PATCHES[idx] = "-d"

    def fetch_patch_options(self: Self, name: str, options_list: list[dict[str, Any]]) -> dict[str, Any]:
        """The function `fetch_patch_options` finds patch options for the patch.

        Parameters
        ----------
        name : str
            Then `name` parameter is a string that represents the name of the patch.
        options_list : list[dict[str, Any]]
            Then `options_list` parameter is a list of dictionary that represents the options for all patches.
        """
        return next(
            filter(lambda obj: obj.get("patchName") == name, options_list),
            {},
        )

    def include_exclude_patch(
        self: Self,
        app: APP,
        patches: list[dict[str, str]],
        patches_dict: dict[str, list[dict[str, str]]],
    ) -> None:
        """The function `include_exclude_patch` includes and excludes patches for a given app."""
        options_list: list[dict[str, Any]] = [{}]
        try:
            with self.config.temp_folder.joinpath(app.options_file).open() as file:
                options_list = json.load(file)
        # Not excepting on JSONDecodeError as it should error out if the file is not a valid JSON
        except FileNotFoundError as e:
            logger.warning(str(e))
            logger.debug("Setting options to empty list.")

        if app.space_formatted:
            for patch in patches:
                normalized_patch = patch["name"].lower().replace(" ", "-")
                (
                    self.include(patch["name"], options_list)
                    if normalized_patch not in app.exclude_request
                    else self.exclude(
                        patch["name"],
                    )
                )
            for patch in patches_dict["universal_patch"]:
                normalized_patch = patch["name"].lower().replace(" ", "-")
                (
                    self.include(
                        patch["name"],
                        options_list,
                    )
                    if normalized_patch in app.include_request
                    else ()
                )
        else:
            for patch in patches:
                (
                    self.include(patch["name"], options_list)
                    if patch["name"] not in app.exclude_request
                    else self.exclude(
                        patch["name"],
                    )
                )
            for patch in patches_dict["universal_patch"]:
                self.include(patch["name"], options_list) if patch["name"] in app.include_request else ()

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
        apk_arg = self.NEW_APK_ARG
        exp = "--force"
        args = [
            self.CLI_JAR,
            app.resource["cli"]["file_name"],
            apk_arg,
            app.download_file_name,
            self.PATCHES_ARG,
            app.resource["patches"]["file_name"],
            self.OUTPUT_ARG,
            app.get_output_file_name(),
            self.KEYSTORE_ARG,
            app.keystore_name,
            exp,
        ]
        args[1::2] = map(self.config.temp_folder.joinpath, args[1::2])
        if app.old_key:
            # https://github.com/ReVanced/revanced-cli/issues/272#issuecomment-1740587534
            old_key_flags = [
                "--keystore-entry-alias=alias",
                "--keystore-entry-password=ReVanced",
                "--keystore-password=ReVanced",
            ]
            args.extend(old_key_flags)
        if self.config.ci_test:
            self.exclude_all_patches()
        if self._PATCHES:
            args.extend(self._PATCHES)
        if app.app_name in self.config.rip_libs_apps:
            excluded = set(possible_archs) - set(app.archs_to_build)
            for arch in excluded:
                args.extend(("--rip-lib", arch))
        args.extend(("--purge",))
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
