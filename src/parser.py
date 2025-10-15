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
    ENABLE_ARG = "-e"
    DISABLE_ARG = "-d"
    EXCLUSIVE_ARG = "--exclusive"

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
        self._PATCHES[:0] = [self.ENABLE_ARG, name]

    def exclude(self: Self, name: str) -> None:
        """The `exclude` function adds a given patch to the list of excluded patches.

        Parameters
        ----------
        name : str
            The `name` parameter is a string that represents the name of the patch to be excluded.
        """
        self._PATCHES.extend([self.DISABLE_ARG, name])
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
                if self._PATCHES[patch_index - 1] == self.ENABLE_ARG:
                    self._PATCHES[patch_index - 1] = self.DISABLE_ARG
                else:
                    self._PATCHES[patch_index - 1] = self.ENABLE_ARG
        except ValueError:
            return False
        else:
            return True

    def enable_exclusive_mode(self: Self) -> None:
        """Enable exclusive mode - only explicitly enabled patches will run, all others disabled by default."""
        logger.info("Enabling exclusive mode for fast testing - only keeping one patch enabled.")
        # Clear all patches and keep only the first one enabled
        if self._PATCHES:
            # Find the first enable argument and its patch name
            for idx in range(0, len(self._PATCHES), 2):
                if idx < len(self._PATCHES) and self._PATCHES[idx] == self.ENABLE_ARG and idx + 1 < len(self._PATCHES):
                    first_patch = self._PATCHES[idx + 1]
                    # Clear all patches and set only the first one
                    self._PATCHES = [self.ENABLE_ARG, first_patch]
                    break

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

    def _load_patch_options(self: Self, app: APP) -> list[dict[str, Any]]:
        """Load patch options from file.

        Parameters
        ----------
        app : APP
            The app instance

        Returns
        -------
        list[dict[str, Any]]
            List of patch options
        """
        options_list: list[dict[str, Any]] = [{}]
        try:
            with self.config.temp_folder.joinpath(app.options_file).open() as file:
                options_list = json.load(file)
        except FileNotFoundError as e:
            logger.warning(str(e))
            logger.debug("Setting options to empty list.")
        return options_list

    def _normalize_patch_name(self: Self, patch_name: str, *, space_formatted: bool) -> str:
        """Normalize patch name based on formatting preference.

        Parameters
        ----------
        patch_name : str
            The original patch name
        space_formatted : bool
            Whether to use space formatting

        Returns
        -------
        str
            Normalized patch name
        """
        return patch_name.lower().replace(" ", "-") if space_formatted else patch_name

    def _should_include_regular_patch(self: Self, patch_name: str, normalized_name: str, app: APP) -> bool:
        """Determine if a regular patch should be included.

        Parameters
        ----------
        patch_name : str
            The original patch name
        normalized_name : str
            The normalized patch name
        app : APP
            The app instance

        Returns
        -------
        bool
            True if patch should be included
        """
        exclude_list = app.exclude_request
        check_name = normalized_name if app.space_formatted else patch_name
        return check_name not in exclude_list

    def _should_include_universal_patch(self: Self, patch_name: str, normalized_name: str, app: APP) -> bool:
        """Determine if a universal patch should be included.

        Parameters
        ----------
        patch_name : str
            The original patch name
        normalized_name : str
            The normalized patch name
        app : APP
            The app instance

        Returns
        -------
        bool
            True if patch should be included
        """
        include_list = app.include_request
        check_name = normalized_name if app.space_formatted else patch_name
        return check_name in include_list

    def _process_regular_patches(
        self: Self,
        patches: list[dict[str, str]],
        app: APP,
        options_list: list[dict[str, Any]],
    ) -> None:
        """Process regular patches for include/exclude.

        Parameters
        ----------
        patches : list[dict[str, str]]
            List of regular patches
        app : APP
            The app instance
        options_list : list[dict[str, Any]]
            List of patch options
        """
        for patch in patches:
            patch_name = patch["name"]
            normalized_name = self._normalize_patch_name(patch_name, space_formatted=app.space_formatted)

            if self._should_include_regular_patch(patch_name, normalized_name, app):
                self.include(patch_name, options_list)
            else:
                self.exclude(patch_name)

    def _process_universal_patches(
        self: Self,
        universal_patches: list[dict[str, str]],
        app: APP,
        options_list: list[dict[str, Any]],
    ) -> None:
        """Process universal patches for include.

        Parameters
        ----------
        universal_patches : list[dict[str, str]]
            List of universal patches
        app : APP
            The app instance
        options_list : list[dict[str, Any]]
            List of patch options
        """
        for patch in universal_patches:
            patch_name = patch["name"]
            normalized_name = self._normalize_patch_name(patch_name, space_formatted=app.space_formatted)

            if self._should_include_universal_patch(patch_name, normalized_name, app):
                self.include(patch_name, options_list)

    def include_exclude_patch(
        self: Self,
        app: APP,
        patches: list[dict[str, str]],
        patches_dict: dict[str, list[dict[str, str]]],
    ) -> None:
        """The function `include_exclude_patch` includes and excludes patches for a given app."""
        options_list = self._load_patch_options(app)

        self._process_regular_patches(patches, app, options_list)
        self._process_universal_patches(patches_dict["universal_patch"], app, options_list)

    def _build_base_args(self: Self, app: APP) -> list[str]:
        """Build base arguments for ReVanced CLI."""
        return [
            self.CLI_JAR,
            app.resource["cli"]["file_name"],
            self.NEW_APK_ARG,
            app.download_file_name,
        ]

    def _add_patch_bundles(self: Self, args: list[str], app: APP) -> None:
        """Add patch bundle arguments to the command."""
        if hasattr(app, "patch_bundles") and app.patch_bundles:
            # Use multiple -p arguments for multiple bundles
            for bundle in app.patch_bundles:
                args.extend([self.PATCHES_ARG, bundle["file_name"]])
        else:
            # Fallback to single bundle for backward compatibility
            args.extend([self.PATCHES_ARG, app.resource["patches"]["file_name"]])

    def _add_output_and_keystore_args(self: Self, args: list[str], app: APP) -> None:
        """Add output file and keystore arguments."""
        args.extend(
            [
                self.OUTPUT_ARG,
                app.get_output_file_name(),
                self.KEYSTORE_ARG,
                app.keystore_name,
                "--force",
            ],
        )

    def _add_keystore_flags(self: Self, args: list[str], app: APP) -> None:
        """Add keystore-specific flags if needed."""
        if app.old_key:
            # https://github.com/ReVanced/revanced-cli/issues/272#issuecomment-1740587534
            old_key_flags = [
                "--keystore-entry-alias=alias",
                "--keystore-entry-password=ReVanced",
                "--keystore-password=ReVanced",
            ]
            args.extend(old_key_flags)

    def _add_architecture_args(self: Self, args: list[str], app: APP) -> None:
        """Add architecture-specific arguments."""
        if app.app_name in self.config.rip_libs_apps:
            excluded = set(possible_archs) - set(app.archs_to_build)
            for arch in excluded:
                args.extend(("--rip-lib", arch))

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
        args = self._build_base_args(app)
        self._add_patch_bundles(args, app)
        self._add_output_and_keystore_args(args, app)

        # Convert paths to absolute paths
        args[1::2] = [str(self.config.temp_folder.joinpath(arg)) for arg in args[1::2]]

        self._add_keystore_flags(args, app)

        if self.config.ci_test:
            self.enable_exclusive_mode()
        if self._PATCHES:
            args.extend(self._PATCHES)

        self._add_architecture_args(args, app)
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
