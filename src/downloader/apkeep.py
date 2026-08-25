"""Apkeep Downloader Class."""

import zipfile
from pathlib import Path
from subprocess import PIPE, Popen
from time import perf_counter
from typing import Any, Self

from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import DownloadError

# Kept for compatibility with a bare `apkeep` source (no explicit provider).
DEFAULT_APKEEP_PROVIDER = "google-play"


class Apkeep(Downloader):
    """Apkeep-based Downloader."""

    @staticmethod
    def _provider_from_source(download_source: str) -> str:
        """Extract apkeep's -d provider from an `apkeep` or `apkeep:<provider>` source string.

        The suffix is passed straight through to apkeep's own -d flag instead of being validated
        against a list this project would have to keep in sync, so any provider apkeep supports
        (google-play, apk-pure, f-droid, huawei-app-gallery, ...) works without a code change here.
        """
        _, _, provider = download_source.partition(":")
        return provider or DEFAULT_APKEEP_PROVIDER

    @staticmethod
    def _apkeep_identifier(package_name: str, version: str) -> str:
        """Build the identifier passed to apkeep's -a flag.

        apkeep names its output file/folder after this exact identifier, so callers must use the same
        value both to invoke apkeep and to know what it will have produced afterward.
        """
        return f"{package_name}@{version}" if version and version != "latest" else package_name

    def _build_apkeep_command(self: Self, app: APP, version: str) -> tuple[list[str], list[str]]:
        """Build the apkeep invocation and a credential-redacted copy safe to log.

        Only Google Play needs account credentials; other providers (F-Droid, APKPure, ...) don't, so
        -e/-t are only included when actually configured rather than required up front.
        """
        provider = self._provider_from_source(app.download_source)
        email = self.config.env.str("APKEEP_EMAIL", "")
        token = self.config.env.str("APKEEP_TOKEN", "")

        cmd = [
            "apkeep",
            "-a",
            self._apkeep_identifier(app.package_name, version),
            "-d",
            provider,
        ]
        if email:
            cmd += ["-e", email]
        if token:
            cmd += ["-t", token]
        cmd += ["-o", "split_apk=true", self.config.temp_folder_name]

        safe_cmd = list(cmd)
        if email:
            safe_cmd[safe_cmd.index(email)] = "<redacted-email>"
        if token:
            safe_cmd[safe_cmd.index(token)] = "<redacted-token>"
        return cmd, safe_cmd

    def _zip_apkeep_output(self: Self, folder_path: Path, zip_path: Path) -> str:
        """Zip apkeep's split-APK output directory into a single archive for the APKEditor merge step."""
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in folder_path.rglob("*"):
                arcname = file.relative_to(self.config.temp_folder)
                zipf.write(file, arcname)
        logger.debug(f"Zipped {folder_path} to {zip_path}")
        return zip_path.name

    def _find_apkeep_output(self: Self, package_name: str) -> Path | None:
        """Locate whatever apkeep just produced for this package.

        apkeep names output after the exact -a identifier (package_name, or package_name@version when
        pinning a version), but that convention isn't verified across every provider, so this falls
        back to matching anything apkeep created for this package rather than failing on a name that's
        merely slightly off. Restricted to plausible identifier boundaries (., @, _) so it can't match
        an unrelated package that happens to share this one as a prefix.
        """
        for candidate in sorted(self.config.temp_folder.glob(f"{package_name}*")):
            if candidate.name != package_name and candidate.name[len(package_name)] not in ".@_":
                continue
            if candidate.is_dir() or candidate.suffix in {".apk", ".xapk", ".zip"}:
                return candidate
        return None

    def _run_apkeep(self: Self, app: APP, version: str = "") -> str:
        """Run apkeep CLI to fetch an APK from whichever provider the app's source selects."""
        package_name = app.package_name
        identifier = self._apkeep_identifier(package_name, version)
        file_path = self.config.temp_folder / f"{identifier}.apk"
        folder_path = self.config.temp_folder / identifier
        zip_path = self.config.temp_folder / f"{identifier}.zip"

        # If already downloaded, return it
        if file_path.exists():
            logger.debug(f"{file_path.name} already downloaded.")
            return file_path.name
        if zip_path.exists():
            logger.debug(f"{zip_path.name} already zipped and exists.")
            return zip_path.name

        cmd, safe_cmd = self._build_apkeep_command(app, version)
        # Keep the exact execution command separate from the log-safe command so credentials never reach CI logs.
        logger.debug(f"Running command: {safe_cmd}")

        start = perf_counter()
        process = Popen(cmd, stdout=PIPE)
        output = process.stdout
        if not output:
            msg = "Failed to send request for patching."
            raise DownloadError(msg)
        for line in output:
            logger.debug(line.decode(), flush=True, end="")
        process.wait()
        if process.returncode != 0:
            msg = f"Command failed with exit code {process.returncode} for app {package_name}"
            raise DownloadError(msg)
        logger.info(f"Downloading completed for app {package_name} in {perf_counter() - start:.2f} seconds.")

        if file_path.exists():
            return file_path.name
        if folder_path.exists() and folder_path.is_dir():
            return self._zip_apkeep_output(folder_path, zip_path)
        if found := self._find_apkeep_output(package_name):
            if found.is_dir():
                return self._zip_apkeep_output(found, zip_path)
            return found.name
        msg = "APK file or folder not found after apkeep execution."
        raise DownloadError(msg)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Download the latest version from the app's apkeep provider."""
        file_name = self._run_apkeep(app)
        logger.info(f"Got file name as {file_name}")
        provider = self._provider_from_source(app.download_source)
        return file_name, f"apkeep://{provider}/{app.package_name}"

    def specific_version(self: Self, app: APP, version: str) -> tuple[str, str]:
        """Download a specific version from the app's apkeep provider.

        Google Play doesn't support this in apkeep; pick a provider that does, e.g. F-Droid or APKPure.
        """
        file_name = self._run_apkeep(app, version)
        logger.info(f"Got file name as {file_name}")
        provider = self._provider_from_source(app.download_source)
        return file_name, f"apkeep://{provider}/{app.package_name}@{version}"
