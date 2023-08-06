"""Status check."""

import requests

from src.patches import Patches
from src.utils import handle_response


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
    output = "New app found which aren't supported yet.<br>"
    for index, app in enumerate(missing_support):
        output += f"{index+1}. [{app}](https://play.google.com/store/apps/details?id={app})<br>"
    print(output)


if __name__ == "__main__":
    main()
