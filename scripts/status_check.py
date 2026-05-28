"""Status check."""

import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from google_play_scraper import app as gplay_app
from google_play_scraper.exceptions import GooglePlayScraperException

from src.cli_args import CLI_PROFILES, append_cli_argument
from src.downloader.sources import (
    APK_MIRROR_BASE_URL,
    APK_MIRROR_PACKAGE_URL,
    PLAY_STORE_APK_URL,
    not_found_icon,
    revanced_api,
)
from src.exceptions import (
    APKMirrorIconScrapError,
    BuilderError,
    DownloadError,
)
from src.patches import Patches
from src.patches_gen import parse_text_to_json, run_command_and_capture_output
from src.utils import apkmirror_status_check, bs4_parser, handle_request_response, request_header, request_timeout

# Updated number of columns from 6 to 5 because Supported? column was removed.
no_of_col = 5
combo_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0"}
github_release_api_headers = {"Accept": "application/vnd.github+json"}
revanced_cli_latest_release_api = "https://api.github.com/repos/ReVanced/revanced-cli/releases/latest"
revanced_cli_file_name = "revanced-cli.jar"
revanced_patches_file_name = "patches.rvp"
download_chunk_size = 1024 * 1024
missing_apps_file = "missing_apps.json"


def _download_file(url: str, destination: Path, headers: dict[str, str] | None = None) -> None:
    """Download an API-selected resource into the temporary status-check workspace."""
    # Streaming keeps the status check memory usage bounded while downloading the CLI and patch bundle.
    with requests.get(url, headers=headers, stream=True, timeout=request_timeout) as response:
        handle_request_response(response, url)
        # The destination lives in a TemporaryDirectory, so direct overwrite is acceptable for this short-lived file.
        with destination.open("wb") as file:
            for chunk in response.iter_content(chunk_size=download_chunk_size):
                # requests can yield keep-alive chunks; skipping empty chunks avoids writing meaningless bytes.
                if chunk:
                    file.write(chunk)


def _latest_revanced_cli_download_url() -> str:
    """Resolve the current ReVanced CLI JAR from GitHub release metadata."""
    response = requests.get(
        revanced_cli_latest_release_api,
        headers=github_release_api_headers,
        timeout=request_timeout,
    )
    handle_request_response(response, revanced_cli_latest_release_api)

    # The release can include signatures or checksums, so match the executable JAR by asset name.
    for asset in response.json()["assets"]:
        asset_name = asset["name"]
        if asset_name.endswith(".jar"):
            return str(asset["browser_download_url"])

    msg = "Unable to find a ReVanced CLI JAR asset in the latest release."
    raise DownloadError(msg, url=revanced_cli_latest_release_api)


def _current_revanced_patches_download_url() -> str:
    """Resolve the v5 patch bundle URL from the ReVanced API release object."""
    response = requests.get(revanced_api, timeout=request_timeout)
    handle_request_response(response, revanced_api)
    # OpenAPI marks `download_url` as required for `/v5/patches`, so missing data should fail loudly.
    return str(response.json()["download_url"])


def _build_v5_list_patches_command(cli_file: Path, patches_file: Path) -> list[str]:
    """Build the ReVanced CLI command that expands a v5 `.rvp` bundle into patch metadata."""
    list_patches_args = CLI_PROFILES["revanced-cli"]["list_patches"]
    command = ["java", "-jar", str(cli_file), list_patches_args["CMD"]]

    # Keep the emitted fields aligned with the existing parser's expected ReVanced-family output.
    for key in ("INDEX", "PACKAGES", "UNIVERSAL", "VERSIONS", "OPTIONS", "DESCRIPTIONS"):
        append_cli_argument(command, list_patches_args.get(key, ""))

    # Status check needs every compatible package, so no package-name filter is emitted here.
    append_cli_argument(command, list_patches_args.get("FILTER_PACKAGE_NAME", ""))
    append_cli_argument(command, list_patches_args["PATCHES"], str(patches_file))
    append_cli_argument(command, list_patches_args["PATCHES_POST"])

    return command


def _list_v5_patches(cli_file: Path, patches_file: Path) -> list[dict[Any, Any]]:
    """List and parse patch metadata from the downloaded v5 patch bundle."""
    output = run_command_and_capture_output(_build_v5_list_patches_command(cli_file, patches_file))
    patches = parse_text_to_json(output)
    # ReVanced CLI may emit non-patch lines, so the status check keeps only parser-confirmed patch entries.
    return sorted((patch for patch in patches if patch["name"] is not None), key=lambda patch: patch["name"])


def _fetch_v5_patches() -> list[dict[Any, Any]]:
    """Download the current v5 resources and return parsed patch metadata."""
    # A temporary directory keeps large downloaded artifacts out of the repository workspace and CI artifacts.
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        cli_file = workspace / revanced_cli_file_name
        patches_file = workspace / revanced_patches_file_name

        _download_file(_latest_revanced_cli_download_url(), cli_file, headers=github_release_api_headers)
        _download_file(
            _current_revanced_patches_download_url(),
            patches_file,
            headers={"Accept": "application/octet-stream"},
        )

        return _list_v5_patches(cli_file, patches_file)


def _compatible_apps_from_patches(patches: list[dict[Any, Any]]) -> set[str]:
    """Collect compatible package names from parsed ReVanced CLI patch metadata."""
    possible_apps: set[str] = set()
    for patch in patches:
        compatible_packages = patch.get("compatiblePackages")
        if not compatible_packages:
            continue
        for compatible_package in compatible_packages:
            # The v5 path uses the repo parser output, where compatible packages are dictionaries with `name`.
            possible_apps.add(compatible_package["name"])
    return possible_apps


def _write_missing_apps_file(missing_support: list[str]) -> None:
    """Write missing packages as compact JSON for downstream automation jobs."""
    # Compact JSON keeps the GitHub Actions job output small enough to pass between jobs without artifacts.
    Path(missing_apps_file).write_text(json.dumps(missing_support, separators=(",", ":")) + "\n", encoding="utf_8")


def bigger_image(possible_links: list[str]) -> str:
    """Select image with higher dimension."""
    higher_dimension_url = ""
    max_dimension = 0

    for url in possible_links:
        dimensions = url.split("_")[-1].split(".")[0].split("x")
        width = int(dimensions[0])
        height = int(dimensions[1])

        area = width * height

        if area > max_dimension:
            max_dimension = area
            higher_dimension_url = url

    return higher_dimension_url



def apkmirror_scrapper(package_name: str) -> str:
    """Apkmirror URL."""
    response = apkmirror_status_check(package_name)
    search_url = APK_MIRROR_PACKAGE_URL.format(package_name)
    if response["data"][0]["exists"]:
        return _extracted_from_apkmirror_scrapper(search_url)
    raise APKMirrorIconScrapError(url=search_url)


def _extracted_from_apkmirror_scrapper(search_url: str) -> str:
    r = requests.get(search_url, headers=request_header, timeout=request_timeout)
    handle_request_response(r, search_url)
    soup = BeautifulSoup(r.text, bs4_parser)
    icon_element = soup.select_one("div.bubble-wrap > img")
    if not icon_element:
        raise APKMirrorIconScrapError(url=search_url)
    sub_url = str(icon_element["src"])
    new_width = 500
    new_height = 500
    new_quality = 100

    # regular expression pattern to match w=xx&h=xx&q=xx
    pattern = r"(w=\d+&h=\d+&q=\d+)"

    return APK_MIRROR_BASE_URL + re.sub(pattern, f"w={new_width}&h={new_height}&q={new_quality}", sub_url)


def gplay_icon_scrapper(package_name: str) -> str:
    """Scrap Icon from Gplay."""
    # noinspection PyBroadException
    try:
        return str(
            gplay_app(
                package_name,
            )["icon"],
        )
    except BuilderError as e:
        raise GooglePlayScraperException from e


def icon_scrapper(package_name: str) -> str:
    """Scrap Icon."""
    scraper_names = {
        "gplay_icon_scrapper": GooglePlayScraperException,
        "apkmirror_scrapper": APKMirrorIconScrapError,
    }

    for scraper_name, error_type in scraper_names.items():
        # noinspection PyBroadException
        try:
            return str(globals()[scraper_name](package_name))
        except error_type:
            pass
        except Exception:  # noqa: BLE001,S110
            pass

    return not_found_icon


def _is_on_apkmirror(package_name: str) -> bool:
    """Helper to check if a package actually exists on APKMirror.

    This queries apkmirror API through the utility function. If the API check fails
    or rate-limits, we default to False to be conservative and prevent workflow crashes.
    """
    try:
        response = apkmirror_status_check(package_name)
        return bool(response["data"][0]["exists"])
    except Exception:
        # Fallback to False if check fails to avoid crashing status script.
        return False


def _is_on_google_play(package_name: str) -> bool:
    """Helper to check if a package actually exists on Google Play.

    This sends a fast HTTP HEAD request to the Play Store. A 200 OK status indicates
    the app is active, while a 404 indicates it is absent or delisted.
    """
    # Build the full URL targeting the app details page on the Play Store.
    url = PLAY_STORE_APK_URL.format(package_name)
    try:
        # We perform a HEAD request rather than a full GET request.
        # This only fetches response headers, bypassing downloading the full HTML page content.
        # It is significantly faster and consumes minimal network bandwidth.
        # We also pass request_header to present a standard User-Agent and prevent requests from being blocked.
        response = requests.head(url, headers=request_header, timeout=request_timeout)
        # HTTP 200 means the app details page is available (app exists).
        # HTTP 404 means the app is not found on Google Play.
        return response.status_code == 200
    except Exception:
        # Fallback to False if check fails (e.g. request timeouts, network failure, or rate limit)
        # to ensure the automated status pipeline never crashes.
        return False


def generate_markdown_table(data: list[list[str]]) -> str:
    """Generate markdown table."""
    if not data:
        return "No data to generate for the table."

    table = (
        "| Package Name | App Icon | PlayStore| APKMirror |Available patches |\n"  # noqa: E501
        "|--------------|----------|----------|-----------|------------------|\n"
    )
    for row in data:
        if len(row) != no_of_col:
            msg = f"Each row must contain {no_of_col} columns of data."
            raise ValueError(msg)

        table += f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |{row[4]} |\n"

    return table


def main() -> None:
    """Entrypoint."""
    patches = _fetch_v5_patches()
    possible_apps = _compatible_apps_from_patches(patches)
    supported_app = set(Patches.support_app().keys())
    missing_support = sorted(possible_apps.difference(supported_app))
    _write_missing_apps_file(missing_support)
    output = "New app found which aren't supported.\n\n"
    data = []
    for app in missing_support:
        # Query APKMirror status API to see if the app exists.
        exists_on_apkmirror = _is_on_apkmirror(app)
        apkmirror_link_text = f"[APKMirror Link]({APK_MIRROR_PACKAGE_URL.format(app)})"
        # Strikethrough (cancelling text) in Markdown is supported via ~~text~~.
        # If the app doesn't exist on APKMirror, we cancel the link.
        if not exists_on_apkmirror:
            apkmirror_link_text = f"~~{apkmirror_link_text}~~"

        # Query Google Play Store scraper to see if the app exists.
        exists_on_google_play = _is_on_google_play(app)
        playstore_link_text = f"[PlayStore Link]({PLAY_STORE_APK_URL.format(app)})"
        # If the app doesn't exist on Google Play, we cancel the link.
        if not exists_on_google_play:
            playstore_link_text = f"~~{playstore_link_text}~~"

        data.append([
            app,
            f'<img src="{icon_scrapper(app)}" width=50 height=50>',
            playstore_link_text,
            apkmirror_link_text,
            f"[Patches](https://revanced.app/patches?pkg={app})",
        ])
    table = generate_markdown_table(data)
    output += table
    with Path("status.md").open("w", encoding="utf_8") as status:
        status.write(output)
    print(output)  # noqa: T201


if __name__ == "__main__":
    main()
