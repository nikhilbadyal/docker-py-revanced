"""Revanced Parser."""
import sys
from subprocess import PIPE, Popen
from time import perf_counter
from typing import List

from loguru import logger

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
        """
        Getter to get all excluded patches
        :return: List of excluded patches
        """
        return self._EXCLUDED

    def get_all_patches(self) -> List[str]:
        """
        Getter to get all excluded patches
        :return: List of excluded patches
        """
        return self._PATCHES

    def invert_patch(self, name: str) -> bool:
        """
        Getter to get all excluded patches
        :return: List of excluded patches
        """
        try:
            patch_index = self._PATCHES.index(name)
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
        app: str,
        version: str,
        is_experimental: bool = False,
        output_prefix: str = "-",
    ) -> None:
        """Revanced APP Patcher.

        :param app: Name of the app
        :param version: Version of the application
        :param is_experimental: Whether to enable experimental support
        :param output_prefix: Prefix to add to the output apks file name
        """
        logger.debug(f"Sending request to revanced cli for building {app} revanced")
        cli = self.config.normal_cli_jar
        patches = self.config.normal_patches_jar
        integrations = self.config.normal_integrations_apk
        if self.config.build_extended and app in self.config.extended_apps:
            cli = self.config.cli_jar
            patches = self.config.patches_jar
            integrations = self.config.integrations_apk
        args = [
            "-jar",
            cli,
            "-a",
            app + ".apk",
            "-b",
            patches,
            "-m",
            integrations,
            "-o",
            f"Re-{app}-{version}{output_prefix}output.apk",
            "--keystore",
            self.config.keystore_name,
            "--options",
            "options.toml",
        ]
        if is_experimental:
            logger.debug("Using experimental features")
            args.append("--experimental")
        args[1::2] = map(lambda i: self.config.temp_folder.joinpath(i), args[1::2])
        if self.config.ci_test:
            self.exclude_all_patches()
        if self._PATCHES:
            args.extend(self._PATCHES)
        if (
            self.config.build_extended
            and len(self.config.archs_to_build) > 0
            and app in self.config.rip_libs_apps
        ):
            excluded = set(possible_archs) - set(self.config.archs_to_build)
            for arch in excluded:
                args.append("--rip-lib")
                args.append(arch)

        start = perf_counter()
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
