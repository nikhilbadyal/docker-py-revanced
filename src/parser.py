import sys
from subprocess import PIPE, Popen
from time import perf_counter
from typing import List

from loguru import logger

from src.config import RevancedConfig
from src.patches import Patches


class Parser(object):
    def __init__(self, patcher: Patches, config: RevancedConfig) -> None:
        self._PATCHES: List[str] = []
        self._EXCLUDED: List[str] = []
        self.patcher = patcher
        self.config = config

    def include(self, name: str) -> None:
        self._PATCHES.extend(["-i", name])

    def exclude(self, name: str) -> None:
        self._PATCHES.extend(["-e", name])
        self._EXCLUDED.append(name)

    def get_excluded_patches(self) -> List[str]:
        return self._EXCLUDED

    def patch_app(self, app: str, version: str, is_experimental: bool = False) -> None:
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
            f"Re-{app}-{version}-output.apk",
            "--keystore",
            self.config.keystore_name,
        ]
        if is_experimental:
            logger.debug("Using experimental features")
            args.append("--experimental")
        args[1::2] = map(lambda i: self.config.temp_folder.joinpath(i), args[1::2])

        if self._PATCHES:
            args.extend(self._PATCHES)

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
