"""Revanced Patches."""
import json
import os
from typing import Any, Dict, List, Tuple

from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.utils import AppNotFound, PatchesJsonFailed


class Patches(object):
    """Revanced Patches."""

    _revanced_app_ids = {
        "com.reddit.frontpage": "reddit",
        "com.ss.android.ugc.trill": "tiktok",
        "com.twitter.android": "twitter",
        "de.dwd.warnapp": "warnwetter",
        "com.spotify.music": "spotify",
        "com.awedea.nyx": "nyx-music-player",
        "ginlemon.iconpackstudio": "icon_pack_studio",
        "com.ticktick.task": "ticktick",
        "tv.twitch.android.app": "twitch",
        "com.myprog.hexedit": "hex-editor",
        "co.windyapp.android": "windy",
        "org.totschnig.myexpenses": "my-expenses",
        "com.backdrops.wallpapers": "backdrops",
        "com.ithebk.expensemanager": "expensemanager",
        "net.dinglisch.android.taskerm": "tasker",
        "net.binarymode.android.irplus": "irplus",
        "com.vsco.cam": "vsco",
        "com.zombodroid.MemeGenerator": "meme-generator-free",
        "com.teslacoilsw.launcher": "nova_launcher",
        "eu.faircode.netguard": "netguard",
        "com.instagram.android": "instagram",
        "com.nis.app": "inshorts",
        "com.facebook.orca": "messenger",
        "com.google.android.apps.recorder": "grecorder",
        "tv.trakt.trakt": "trakt",
        "com.candylink.openvpn": "candyvpn",
        "com.sony.songpal.mdr": "sonyheadphone",
        "com.dci.dev.androidtwelvewidgets": "androidtwelvewidgets",
        "io.yuka.android": "yuka",
        "free.reddit.news": "relay",
        "com.rubenmayayo.reddit": "boost",
        "com.andrewshu.android.reddit": "rif",
        "com.laurencedawson.reddit_sync": "sync",
        "ml.docilealligator.infinityforreddit": "infinity",
        "me.ccrama.redditslide": "slide",
        "com.onelouder.baconreader": "bacon",
        "com.google.android.youtube": "youtube",
        "com.google.android.apps.youtube.music": "youtube_music",
        "com.mgoogle.android.gms": "microg",
        "jp.pxv.android": "pixiv",
    }
    revanced_app_ids = {
        key: (value, "_" + value) for key, value in _revanced_app_ids.items()
    }

    @staticmethod
    def support_app() -> Dict[str, str]:
        """Return supported apps."""
        return Patches._revanced_app_ids

    def scrap_patches(self, file_name: str) -> Any:
        """Scrap Patches."""
        if os.path.exists(file_name):
            with open(file_name) as f:
                patches = json.load(f)
            return patches
        raise PatchesJsonFailed()

    # noinspection DuplicatedCode
    def fetch_patches(self, config: RevancedConfig, app: APP) -> None:
        """Function to fetch all patches."""
        patches = self.scrap_patches(
            f'{config.temp_folder}/{app.resource["patches_json"]}'
        )
        for app_name in (self.revanced_app_ids[x][1] for x in self.revanced_app_ids):
            setattr(self, app_name, [])
        setattr(self, "universal_patch", [])

        for patch in patches:
            if not patch["compatiblePackages"]:
                p = {x: patch[x] for x in ["name", "description"]}
                p["app"] = "universal"
                p["version"] = "all"
                getattr(self, "universal_patch").append(p)
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in self.revanced_app_ids:
                    app_name = self.revanced_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)
        n_patches = len(getattr(self, f"_{app.app_name}"))
        app.no_of_patches = n_patches

    def __init__(self, config: RevancedConfig, app: APP) -> None:
        self.fetch_patches(config, app)

    def get(self, app: str) -> Tuple[List[Dict[str, str]], str]:
        """Get all patches for the given app.

        :param app: Name of the application
        :return: Patches
        """
        app_names = {value[0]: value[1] for value in self.revanced_app_ids.values()}

        if not (app_name := app_names.get(app)):
            raise AppNotFound(app)
        patches = getattr(self, app_name)
        version = "latest"
        try:
            version = next(i["version"] for i in patches if i["version"] != "all")
        except StopIteration:
            pass
        return patches, version

    # noinspection IncorrectFormatting
    def include_exclude_patch(
        self, app: APP, parser: Any, patches: List[Dict[str, str]]
    ) -> None:
        """Include and exclude patches for a given app.

        :param app: Name of the app
        :param parser: Parser Obj
        :param patches: All the patches of a given app
        """
        for patch in patches:
            normalized_patch = patch["name"].lower().replace(" ", "-")
            parser.include(
                normalized_patch
            ) if normalized_patch not in app.exclude_request else parser.exclude(
                normalized_patch
            )
        for normalized_patch in app.include_request:
            parser.include(normalized_patch) if normalized_patch not in getattr(
                self, "universal_patch", []
            ) else ()
        logger.info(app)

    def get_app_configs(self, app: "APP") -> List[Dict[str, str]]:
        """Get Configurations for a given app.

        :param app: Name of the application
        :return: All Patches , Its version and whether it is
            experimental
        """
        experiment = False
        total_patches, recommended_version = self.get(app=app.app_name)
        if app.app_version:
            logger.debug(f"Picked {app} version {app.app_version:} from env.")
            if (
                app.app_version == "latest"
                or app.app_version > recommended_version
                or app.app_version < recommended_version
            ):
                experiment = True
            recommended_version = app.app_version
        app.set_recommended_version(recommended_version, experiment)
        return total_patches
