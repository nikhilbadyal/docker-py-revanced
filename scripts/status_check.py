"""Status check."""

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag
from google_play_scraper import app as gplay_app
from google_play_scraper.exceptions import GooglePlayScraperException

from src.downloader.sources import (
    APK_COMBO_GENERIC_URL,
    APK_MIRROR_BASE_URL,
    APK_MIRROR_PACKAGE_URL,
    APK_MONK_APK_URL,
    APK_MONK_ICON_URL,
    APK_PURE_ICON_URL,
    PLAY_STORE_APK_URL,
    not_found_icon,
    revanced_api,
)
from src.exceptions import (
    APKComboIconScrapError,
    APKMirrorIconScrapError,
    APKMonkIconScrapError,
    APKPureIconScrapError,
    BuilderError,
    ScrapingError,
)
from src.patches import Patches
from src.utils import apkmirror_status_check, bs4_parser, handle_request_response, request_header, request_timeout

no_of_col = 8
combo_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0"}


def apkcombo_scrapper(package_name: str) -> str:
    """Apkcombo scrapper."""
    apkcombo_url = APK_COMBO_GENERIC_URL.format(package_name)
    try:
        r = requests.get(apkcombo_url, headers=combo_headers, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, apkcombo_url)
        soup = BeautifulSoup(r.text, bs4_parser)
        avatar = soup.find(class_="avatar")
        if not isinstance(avatar, Tag):
            raise APKComboIconScrapError(url=apkcombo_url)
        icon_element = avatar.find("img")
        if not isinstance(icon_element, Tag):
            raise APKComboIconScrapError(url=apkcombo_url)
        url = icon_element.get("data-src")
        return re.sub(r"=.*$", "", url)  # type: ignore[arg-type]
    except BuilderError as e:
        raise APKComboIconScrapError(url=apkcombo_url) from e


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


def apkmonk_scrapper(package_name: str) -> str:
    """APKMonk scrapper."""
    apkmonk_url = APK_MONK_APK_URL.format(package_name)
    icon_logo = APK_MONK_ICON_URL.format(package_name)
    r = requests.get(apkmonk_url, headers=combo_headers, allow_redirects=True, timeout=request_timeout)
    handle_request_response(r, apkmonk_url)
    if head := BeautifulSoup(r.text, bs4_parser).head:
        parsed_head = BeautifulSoup(str(head), bs4_parser)
        href_elements = parsed_head.find_all(href=True)
        possible_link = []
        for element in href_elements:
            href_value = element.get("href")
            if href_value.startswith(icon_logo):
                possible_link.append(href_value)
        if possible_link:
            return bigger_image(possible_link)
    raise APKMonkIconScrapError(url=apkmonk_url)


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


def apkpure_scrapper(package_name: str) -> str:
    """Scrap Icon from apkpure."""
    apkpure_url = APK_PURE_ICON_URL.format(package_name)
    try:
        r = requests.get(apkpure_url, headers=combo_headers, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, apkpure_url)
        soup = BeautifulSoup(r.text, bs4_parser)
        search_result = soup.find_all(class_="brand-info-top")
        for brand_info in search_result:
            if icon_element := brand_info.find(class_="icon"):
                return str(icon_element.get("src"))
        raise APKPureIconScrapError(url=apkpure_url)
    except BuilderError as e:
        raise APKPureIconScrapError(url=apkpure_url) from e


def icon_scrapper(package_name: str) -> str:
    """Scrap Icon."""
    scraper_names = {
        "gplay_icon_scrapper": GooglePlayScraperException,
        "apkmirror_scrapper": APKMirrorIconScrapError,
        "apkmonk_scrapper": APKMonkIconScrapError,
        "apkpure_scrapper": APKPureIconScrapError,
        "apkcombo_scrapper": APKComboIconScrapError,
    }

    for scraper_name, error_type in scraper_names.items():
        try:
            return str(globals()[scraper_name](package_name))
        except error_type:
            pass
        except ScrapingError:
            pass

    return not_found_icon


def generate_markdown_table(data: list[list[str]]) -> str:
    """Generate markdown table."""
    if not data:
        return "No data to generate for the table."

    table = (
        "| Package Name | App Icon | PlayStore| APKMirror |APKMonk |ApkPure | ApkCombo |Supported?|\n"
        "|--------------|----------|----------|-----------|--------|--------|----------|----------|\n"
    )
    for row in data:
        if len(row) != no_of_col:
            msg = f"Each row must contain {no_of_col} columns of data."
            raise ValueError(msg)

        table += f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |{row[4]} |{row[5]} | {row[6]} | {row[7]} |\n"

    return table


def main() -> None:
    """Entrypoint."""
    response = requests.get(revanced_api, timeout=request_timeout)
    handle_request_response(response, revanced_api)

    patches = response.json()["patches"]

    possible_apps = set()
    for patch in patches:
        if patch.get("compatiblePackages", None):
            for compatible_package in patch["compatiblePackages"]:
                possible_apps.add(compatible_package["name"])

    supported_app = set(Patches.support_app().keys())
    missing_support = sorted(possible_apps.difference(supported_app))
    output = "New app found which aren't supported.\n\n"
    data = [
        [
            app,
            f'<img src="{icon_scrapper(app)}" width=50 height=50>',
            f"[PlayStore Link]({PLAY_STORE_APK_URL.format(app)})",
            f"[APKMirror Link]({APK_MIRROR_PACKAGE_URL.format(app)})",
            f"[APKMonk Link]({APK_MONK_APK_URL.format(app)})",
            f"[APKPure Link]({APK_PURE_ICON_URL.format(app)})",
            f"[APKCombo Link]({APK_COMBO_GENERIC_URL.format(app)})",
            "<li>- [ ] </li>",
        ]
        for app in missing_support
    ]
    table = generate_markdown_table(data)
    output += table
    with Path("status.md").open("w", encoding="utf_8") as status:
        status.write(output)
    print(output)  # noqa: T201


if __name__ == "__main__":
    main()
