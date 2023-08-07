"""Status check."""
from typing import List

import requests
from google_play_scraper import app as gplay_app

from src.patches import Patches
from src.utils import handle_response

not_found_icon = "https://img.icons8.com/bubbles/500/android-os.png"


def gplay_icon_scrapper(package_name: str) -> str:
    """Scrap Icon from Gplay."""
    # noinspection PyBroadException
    try:
        result = gplay_app(
            package_name,
        )
        if not result["icon"]:
            raise ValueError()
        return str(result["icon"])
    except Exception:
        return not_found_icon


def generate_markdown_table(data: List[List[str]]) -> str:
    """Generate table."""
    if len(data) == 0:
        return "No data to generate table."

    table = "| Package Name | App Icon | PlayStore link | APKMirror link| Supported?|\n"
    table += (
        "|-------------|----------|----------------|---------------|------------|\n"
    )

    for row in data:
        if len(row) != 5:
            raise ValueError("Each row must contain 4 columns of data.")

        table += f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |{row[4]} |\n"

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
    output = "New app found which aren't supported or outdated.\n\n"
    data = []
    for index, app in enumerate(missing_support):
        data.append(
            [
                app,
                f'<img src="{gplay_icon_scrapper(app)}" width=50 height=50>',
                f"[PlayStore Link](https://play.google.com/store/apps/details?id={app})",
                f"[APKMirror Link](https://www.apkmirror.com/?s={app})",
                "<li>- [ ] </li>",
            ]
        )
    table = generate_markdown_table(data)
    output += table
    print(output)


if __name__ == "__main__":
    main()
