"""Status check."""
import re
from typing import List

import requests
from bs4 import BeautifulSoup
from google_play_scraper import app as gplay_app
from google_play_scraper.exceptions import GooglePlayScraperException

from src.exceptions import APKMirrorIconScrapFailure
from src.patches import Patches
from src.utils import (
    apk_mirror_base_url,
    apkmirror_status_check,
    bs4_parser,
    handle_request_response,
    request_header,
)

not_found_icon = "https://img.icons8.com/bubbles/500/android-os.png"


def apkcombo_scrapper(package_name: str) -> str:
    """Apkcombo scrapper."""
    try:
        apkcombo_url = f"https://apkcombo.com/genericApp/{package_name}"
        r = requests.get(
            apkcombo_url, headers=request_header, allow_redirects=True, timeout=10
        )
        soup = BeautifulSoup(r.text, bs4_parser)
        url = soup.select_one("div.avatar > img")["data-src"]
        return re.sub(r"=.*$", "", url)
    except Exception:
        return not_found_icon


def apkmirror_scrapper(package_name: str) -> str:
    """Apkmirror URL."""
    response = apkmirror_status_check(package_name)
    search_url = f"{apk_mirror_base_url}/?s={package_name}"
    if response["data"][0]["exists"]:
        return _extracted_from_apkmirror_scrapper(search_url)
    raise APKMirrorIconScrapFailure(url=search_url)


def _extracted_from_apkmirror_scrapper(search_url: str) -> str:
    r = requests.get(search_url, headers=request_header, timeout=60)
    soup = BeautifulSoup(r.text, bs4_parser)
    sub_url = soup.select_one("div.bubble-wrap > img")["src"]
    new_width = 500
    new_height = 500
    new_quality = 100

    # regular expression pattern to match w=xx&h=xx&q=xx
    pattern = r"(w=\d+&h=\d+&q=\d+)"

    return apk_mirror_base_url + re.sub(
        pattern, f"w={new_width}&h={new_height}&q={new_quality}", sub_url
    )


def gplay_icon_scrapper(package_name: str) -> str:
    """Scrap Icon from Gplay."""
    # noinspection PyBroadException
    try:
        result = gplay_app(
            package_name,
        )
        if result["icon"]:
            return str(result["icon"])
        raise GooglePlayScraperException()
    except GooglePlayScraperException:
        try:
            return apkmirror_scrapper(package_name)
        except APKMirrorIconScrapFailure:
            return apkcombo_scrapper(package_name)
    except Exception:
        return not_found_icon


def generate_markdown_table(data: List[List[str]]) -> str:
    """Generate table."""
    if not data:
        return "No data to generate table."

    table = (
        "| Package Name | App Icon | PlayStore link | APKMirror link|APKCombo Link| Supported?|\n"
        + "|-------------|----------|----------------|---------------|------------------|----------|\n"
    )
    for row in data:
        if len(row) != 6:
            raise ValueError("Each row must contain 6 columns of data.")

        table += f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |{row[4]} |{row[5]} |\n"

    return table


def main() -> None:
    repo_url = "https://releases.revanced.app/patches"
    response = requests.get(repo_url, timeout=10)
    handle_request_response(response)

    patches = response.json()

    possible_apps = set()
    for patch in patches:
        for compatible_package in patch["compatiblePackages"]:
            possible_apps.add(compatible_package["name"])

    supported_app = set(Patches.support_app().keys())
    missing_support = sorted(possible_apps.difference(supported_app))
    output = "New app found which aren't supported or outdated.\n\n"
    data = [
        [
            app,
            f'<img src="{gplay_icon_scrapper(app)}" width=50 height=50>',
            f"[PlayStore Link](https://play.google.com/store/apps/details?id={app})",
            f"[APKMirror Link](https://www.apkmirror.com/?s={app})",
            f"[APKCombo Link](https://apkcombo.com/genericApp/{app})",
            "<li>- [ ] </li>",
        ]
        for app in missing_support
    ]
    table = generate_markdown_table(data)
    output += table
    with open("status.md", "w", encoding="utf_8") as status:
        status.write(output)
    print(output)


if __name__ == "__main__":
    main()
