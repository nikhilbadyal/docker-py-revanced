"""Revanced Parser."""
import sys
from subprocess import PIPE, Popen
from time import perf_counter
from typing import List

from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.patches import Patches
from src.utils import possible_archs


class Parser(object):
    """Revanced Parser."""

    def __init__(self, patcher: Patches, config: RevancedConfig) -> None:
        self._PATCHES: List[str] = []
        self._EXCLUDED: List[str] = []
        self.patcher = patcher
        self.config = config

    def include(self, name: str) -> None:
        """Include a given patch.

        :param name: Name of the patch
        """
        self._PATCHES.extend(["-i", name])

    def exclude(self, name: str) -> None:
        """Exclude a given patch.

        :param name: Name of the patch to exclude
        """
        self._PATCHES.extend(["-e", name])
        self._EXCLUDED.append(name)

    def get_excluded_patches(self) -> List[str]:
        """Getter to get all excluded patches :return: List of excluded
        patches."""
        return self._EXCLUDED

    def get_all_patches(self) -> List[str]:
        """Getter to get all excluded patches :return: List of excluded
        patches."""
        return self._PATCHES

    def invert_patch(self, name: str) -> bool:
        """Getter to get all excluded patches :return: List of excluded
        patches."""
        try:
            name = name.lower().replace(" ", "-")
            patch_index = self._PATCHES.index(name)
            indices = [i for i in range(len(self._PATCHES)) if self._PATCHES[i] == name]
            for patch_index in indices:
                if self._PATCHES[patch_index - 1] == "-e":
                    self._PATCHES[patch_index - 1] = "-i"
                else:
                    self._PATCHES[patch_index - 1] = "-e"
            return True
        except ValueError:
            return False

    def exclude_all_patches(self) -> None:
        """Exclude all patches to Speed up CI."""
        for idx, item in enumerate(self._PATCHES):
            if item == "-i":
                self._PATCHES[idx] = "-e"

    # noinspection IncorrectFormatting
    def patch_app(
        self,
        app: APP,
    ) -> None:
        """Revanced APP Patcher.

        :param app: Name of the app
        """
        args = [
            "-jar",
            app.resource["cli"],
            "-a",
            f"{app.app_name}.apk",
            "-b",
            app.resource["patches"],
            "-m",
            app.resource["integrations"],
            "-o",
            app.get_output_file_name(),
            "--keystore",
            app.keystore_name,
            "--options",
            "options.json",
        ]
        if app.experiment:
            logger.debug("Using experimental features")
            args.append("--experimental")
        args[1::2] = map(self.config.temp_folder.joinpath, args[1::2])
        if self.config.ci_test:
            self.exclude_all_patches()
        if self._PATCHES:
            args.extend(self._PATCHES)
        if app.app_name in self.config.rip_libs_apps:
            excluded = set(possible_archs) - set(app.archs_to_build)
            for arch in excluded:
                args.extend(("--rip-lib", arch))
        start = perf_counter()
        logger.debug(
            f"Sending request to revanced cli for building with args java {args}"
        )
        process = Popen(["java", *args], stdout=PIPE)
        output = process.stdout
        if not output:
            logger.error("Failed to send request for patching.")
            sys.exit(-1)
        for line in output:
            logger.debug(line.decode(), flush=True, end="")
        process.wait()
        logger.info(
            f"Patching completed for app {app} in {perf_counter() - start:.2f} seconds."
        )
