"""Status check."""
from typing import List

import requests
from bs4 import BeautifulSoup

from src.patches import Patches
from src.utils import handle_response

not_found_icon = "https://img.icons8.com/bubbles/500/android-os.png"


def gplay_icon_scrapper(package_name: str) -> str:
    """Scrap Icon from Gplay."""
    # noinspection PyBroadException
    try:
        app_url = (
            f"https://play.google.com/store/apps/details?id={package_name}&hl=en&gl=US"
        )
        response = requests.get(app_url)
        soup = BeautifulSoup(response.text, "html.parser")
        icon = soup.select_one("div.Il7kR > img")
        return str(icon["srcset"].split(" ")[0])
    except Exception:
        return not_found_icon


def generate_markdown_table(data: List[List[str]]) -> str:
    """Generate table."""
    if len(data) == 0:
        return "No data to generate table."

    table = "| Package Name | PlayStore link | APKMirror link| Supported ?|\n"
    table += "|-------------|----------------|---------------|------------|\n"

    for row in data:
        if len(row) != 3:
            raise ValueError("Each row must contain 4 columns of data.")

        table += f"| {row[0]} | {row[1]} | {row[2]} | <li>- [ ] </li> |\n"

    return table


def main() -> None:
    repo_url = "https://api.revanced.app/v2/patches/latest"
    response = requests.get(repo_url)
    handle_response(response)

    parsed_data = response.json()
    compatible_packages = parsed_data["patches"]

    possible_apps = set()
    for package in compatible_packages:
        for compatible_package in package["compatiblePackages"]:
            possible_apps.add(compatible_package["name"])

    supported_app = set(Patches.support_app().keys())
    missing_support = possible_apps.difference(supported_app)
    output = "New app found which aren't supported yet.\n\n"
    data = []
    for index, app in enumerate(missing_support):
        data.append(
            [
                f'<img src="{gplay_icon_scrapper(app)}" width=50 height=50>',
                f"[PlayStore Link](https://play.google.com/store/apps/details?id={app})",
                f"[APKMirror Link](https://www.apkmirror.com/?s={app})",
            ]
        )
    table = generate_markdown_table(data)
    output += table
    print(output)


if __name__ == "__main__":
    main()
