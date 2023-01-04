"""Revanced Patches."""
import subprocess
from typing import Any, Dict, List, Tuple

from loguru import logger
from requests import Session

from src.config import RevancedConfig
from src.utils import AppNotFound, handle_response


class Patches(object):
    """Revanced Patches."""

    revanced_app_ids = {
        "com.reddit.frontpage": ("reddit", "_reddit"),
        "com.ss.android.ugc.trill": ("tiktok", "_tiktok"),
        "com.twitter.android": ("twitter", "_twitter"),
        "de.dwd.warnapp": ("warnwetter", "_warnwetter"),
        "com.spotify.music": ("spotify", "_spotify"),
        "com.awedea.nyx": ("nyx-music-player", "_nyx"),
        "ginlemon.iconpackstudio": ("icon_pack_studio", "_iconpackstudio"),
        "com.ticktick.task": ("ticktick", "_ticktick"),
        "tv.twitch.android.app": ("twitch", "_twitch"),
        "com.myprog.hexedit": ("hex-editor", "_hexeditor"),
        "org.citra.citra_emu": ("citra", "_citra"),
        "co.windyapp.android": ("windy", "_windy"),
        "org.totschnig.myexpenses": ("my-expenses", "_expenses"),
        "com.backdrops.wallpapers": ("backdrops", "_backdrops"),
        "com.ithebk.expensemanager": ("expensemanager", "_expensemanager"),
        "net.dinglisch.android.taskerm": ("tasker", "_tasker"),
    }
    revanced_extended_app_ids = {
        "com.google.android.youtube": ("youtube", "_yt"),
        "com.google.android.apps.youtube.music": ("youtube-music", "_ytm"),
    }

    @staticmethod
    def check_java() -> None:
        """Check if Java17 is installed."""
        try:
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
        except subprocess.CalledProcessError:
            logger.debug("Java 17 Must be installed")
            exit(-1)

    # noinspection DuplicatedCode
    def fetch_patches(self) -> None:
        """Function to fetch all patches."""
        session = Session()

        logger.debug("fetching all patches")
        response = session.get(
            "https://raw.githubusercontent.com/revanced/revanced-patches/main/patches.json"
        )
        handle_response(response)
        patches = response.json()

        for app_name in (self.revanced_app_ids[x][1] for x in self.revanced_app_ids):
            setattr(self, app_name, [])

        for patch in patches:
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in self.revanced_app_ids:
                    app_name = self.revanced_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)
        if self.config.build_extended:
            url = "https://raw.githubusercontent.com/inotia00/revanced-patches/revanced-extended/patches.json"
        else:
            url = "https://raw.githubusercontent.com/revanced/revanced-patches/main/patches.json"

        response = session.get(url)
        handle_response(response)
        extended_patches = response.json()
        for app_name in (
            self.revanced_extended_app_ids[x][1] for x in self.revanced_extended_app_ids
        ):
            setattr(self, app_name, [])

        for patch in extended_patches:
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in self.revanced_extended_app_ids:
                    app_name = self.revanced_extended_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)

        for app_name, app_id in self.revanced_extended_app_ids.values():
            n_patches = len(getattr(self, app_id))
            logger.debug(f"Total patches in {app_name} are {n_patches}")
        for app_name, app_id in self.revanced_app_ids.values():
            n_patches = len(getattr(self, app_id))
            logger.debug(f"Total patches in {app_name} are {n_patches}")

    def __init__(self, config: RevancedConfig) -> None:
        self.config = config
        self.check_java()
        self.fetch_patches()

    def get(self, app: str) -> Tuple[List[Dict[str, str]], str]:
        """Get all patches for the given app.

        :param app: Name of the application
        :return: Patches
        """
        logger.debug("Getting patches for %s" % app)
        app_names = {
            "reddit": "_reddit",
            "tiktok": "_tiktok",
            "twitter": "_twitter",
            "warnwetter": "_warnwetter",
            "youtube": "_yt",
            "youtube_music": "_ytm",
            "spotify": "_spotify",
            "nyx-music-player": "_nyx",
            "icon_pack_studio": "_iconpackstudio",
            "ticktick": "_ticktick",
            "twitch": "_twitch",
            "hex-editor": "_hexeditor",
            "citra": "_citra",
            "windy": "_windy",
            "my-expenses": "_expenses",
            "backdrops": "_backdrops",
            "expensemanager": "_expensemanager",
            "tasker": "_tasker",
        }
        if not (app_name := app_names.get(app)):
            raise AppNotFound(app)
        patches = getattr(self, app_name)
        version = ""
        try:
            if app in ("youtube", "youtube_music"):
                version = next(i["version"] for i in patches if i["version"] != "all")
                logger.debug(f"Recommended Version for patching {app} is {version}")
            else:
                logger.debug("No recommended version.")
        except StopIteration:
            pass  # No recommended version available
        return patches, version

    # noinspection IncorrectFormatting
    def include_exclude_patch(
        self, app: str, parser: Any, patches: List[Dict[str, str]]
    ) -> None:
        """Include and exclude patches for a given app.

        :param app: Name of the app
        :param parser: Parser Obj
        :param patches: All the patches of a given app
        """
        logger.debug(f"Excluding patches for app {app}")
        if self.config.build_extended and app in self.config.extended_apps:
            excluded_patches = self.config.env.list(
                f"EXCLUDE_PATCH_{app}_EXTENDED".upper(), []
            )
        else:
            excluded_patches = self.config.env.list(f"EXCLUDE_PATCH_{app}".upper(), [])
        for patch in patches:
            parser.include(patch["name"]) if patch[
                "name"
            ] not in excluded_patches else parser.exclude(patch["name"])
        excluded = parser.get_excluded_patches()
        if excluded:
            logger.debug(f"Excluded patches {excluded} for {app}")
        else:
            logger.debug(f"No excluded patches for {app}")

    def get_app_configs(self, app: str) -> Tuple[List[Dict[str, str]], str, bool]:
        """Get Configurations for a given app.

        :param app: Name of the application
        :return: All Patches , Its version and whether it is experimental
        """
        experiment = False
        total_patches, recommended_version = self.get(app=app)
        env_version = self.config.env.str(f"{app}_VERSION".upper(), None)
        if env_version:
            logger.debug(f"Picked {app} version {env_version} from env.")
            if (
                env_version == "latest"
                or env_version > recommended_version
                or env_version < recommended_version
            ):
                experiment = True
            recommended_version = env_version
        return total_patches, recommended_version, experiment
