"""Update preferred apps."""

import os

import dotenv
from loguru import logger


def update_patch_apps() -> None:
    """Update preferred apps."""
    dotenv_file = dotenv.find_dotenv()
    dotenv.load_dotenv(dotenv_file)
    patch_apps = os.environ["PATCH_APPS"]
    logger.info(f"PATCH_APPS is currently {patch_apps}")
    os.environ["PATCH_APPS"] = os.environ["PREFERRED_PATCH_APPS"]
    new_patch_apps = os.environ["PATCH_APPS"]
    logger.info(f"PATCH_APPS is now {new_patch_apps}")

    dotenv.set_key(dotenv_file, "PATCH_APPS", os.environ["PATCH_APPS"])


if __name__ == "__main__":
    update_patch_apps()
