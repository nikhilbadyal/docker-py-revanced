import subprocess
import sys
from typing import Any, Dict, List, Tuple

from loguru import logger
from requests import Session

from src.config import RevancedConfig


class Patches(object):
    def check_java(self) -> None:
        logger.debug("Checking if java is available")
        jd = subprocess.check_output(
            ["java", "-version"], stderr=subprocess.STDOUT
        ).decode("utf-8")
        jd = jd[1:-1]
        if "Runtime Environment" not in jd:
            logger.debug("Java Must be installed")
            exit(-1)
        if "17" not in jd:
            logger.debug("Java 17 Must be installed")
            exit(-1)
        logger.debug("Cool!! Java is available")

    def fetch_patches(self) -> None:
        session = Session()

        logger.debug("fetching all patches")
        resp = session.get(
            "https://raw.githubusercontent.com/revanced/revanced-patches/main/patches.json"
        )
        patches = resp.json()

        revanced_app_ids = {
            "com.reddit.frontpage": ("reddit", "_reddit"),
            "com.ss.android.ugc.trill": ("tiktok", "_tiktok"),
            "com.twitter.android": ("twitter", "_twitter"),
            "de.dwd.warnapp": ("warnwetter", "_warnwetter"),
            "com.spotify.music": ("spotify", "_spotify"),
        }

        for app_name in (revanced_app_ids[x][1] for x in revanced_app_ids):
            setattr(self, app_name, [])

        for patch in patches:
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in revanced_app_ids:
                    app_name = revanced_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)
        if self.config.build_extended:
            url = "https://raw.githubusercontent.com/inotia00/revanced-patches/revanced-extended/patches.json"
        else:
            url = "https://raw.githubusercontent.com/revanced/revanced-patches/main/patches.json"

        resp_extended = session.get(url)
        extended_patches = resp_extended.json()
        revanced_extended_app_ids = {
            "com.google.android.youtube": ("youtube", "_yt"),
            "com.google.android.apps.youtube.music": ("youtube-music", "_ytm"),
        }
        for app_name in (
            revanced_extended_app_ids[x][1] for x in revanced_extended_app_ids
        ):
            setattr(self, app_name, [])

        for patch in extended_patches:
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in revanced_extended_app_ids:
                    app_name = revanced_extended_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)

        for app_name, app_id in revanced_extended_app_ids.values():
            n_patches = len(getattr(self, app_id))
            logger.debug(f"Total patches in {app_name} are {n_patches}")
        for app_name, app_id in revanced_app_ids.values():
            n_patches = len(getattr(self, app_id))
            logger.debug(f"Total patches in {app_name} are {n_patches}")

    def __init__(self, config: RevancedConfig) -> None:
        self.config = config
        self.check_java()
        self.fetch_patches()

    def get(self, app: str) -> Tuple[List[Dict[str, str]], str]:
        logger.debug("Getting patches for %s" % app)
        app_names = {
            "reddit": "_reddit",
            "tiktok": "_tiktok",
            "twitter": "_twitter",
            "warnwetter": "_warnwetter",
            "youtube": "_yt",
            "youtube_music": "_ytm",
            "spotify": "_spotify",
        }
        if not (app_name := app_names.get(app)):
            logger.debug("Invalid app name")
            sys.exit(-1)
        patches = getattr(self, app_name)
        version = ""
        if app in ("youtube", "youtube_music"):
            version = next(i["version"] for i in patches if i["version"] != "all")
            logger.debug(f"Recommended Version for patching {app} is {version}")
        else:
            logger.debug("No recommended version.")
        return patches, version

    def include_and_exclude_patches(
        self, app: str, arg_parser: Any, app_patches: List[Dict[str, str]]
    ) -> None:
        logger.debug(f"Excluding patches for app {app}")
        if self.config.build_extended and app in self.config.extended_apps:
            excluded_patches = self.config.env.list(
                f"EXCLUDE_PATCH_{app}_EXTENDED".upper(), []
            )
        else:
            excluded_patches = self.config.env.list(f"EXCLUDE_PATCH_{app}".upper(), [])
        for patch in app_patches:
            arg_parser.include(patch["name"]) if patch[
                "name"
            ] not in excluded_patches else arg_parser.exclude(patch["name"])
        excluded = arg_parser.get_excluded_patches()
        if excluded:
            logger.debug(f"Excluded patches {excluded} for {app}")
        else:
            logger.debug(f"No excluded patches for {app}")

    def get_app_configs(self, app: str) -> Tuple[List[Dict[str, str]], str, bool]:
        experiment = False
        total_patches, recommended_version = self.get(app=app)
        env_version = self.config.env.str(f"{app}_VERSION".upper(), None)
        if env_version:
            logger.debug(f"Picked {app} version {env_version} from env.")
            if env_version == "latest" or env_version > recommended_version:
                experiment = True
            recommended_version = env_version
        return total_patches, recommended_version, experiment
