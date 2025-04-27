"""Revanced Patches."""

import contextlib
from typing import ClassVar, Self

from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.exceptions import AppNotFoundError
from src.patches_gen import convert_command_output_to_json


class Patches(object):
    """Revanced Patches."""

    revanced_package_names: ClassVar[dict[str, str]] = {
        "com.reddit.frontpage": "reddit",
        "com.duolingo": "duolingo",
        "com.ss.android.ugc.trill": "tiktok",
        "com.zhiliaoapp.musically": "musically",
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
        "pl.solidexplorer2": "solidexplorer",
        "com.adobe.lrmobile": "lightroom",
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
        "com.strava": "strava",
        "com.microblink.photomath": "photomath",
        "o.o.joey": "joey",
        "com.vanced.android.youtube": "vanced",
        "com.spotify.lite": "spotify-lite",
        "at.gv.oe.app": "digitales",
        "com.scb.phone": "scbeasy",
        "reddit.news": "reddit-news",
        "at.gv.bmf.bmf2go": "finanz-online",
        "com.tumblr": "tumblr",
        "com.myfitnesspal.android": "fitnesspal",
        "com.facebook.katana": "facebook",
        "io.syncapps.lemmy_sync": "lemmy-sync",
        "com.xiaomi.wearable": "xiaomi-wearable",
        "com.google.android.apps.photos": "photos",
        "com.amazon.mShop.android.shopping": "amazon",
        "com.bandcamp.android": "bandcamp",
        "com.google.android.apps.magazines": "magazines",
        "com.rarlab.rar": "winrar",
        "com.soundcloud.android": "soundcloud",
        "de.stocard.stocard": "stocard",
        "at.willhaben": "willhaben",
        "ch.protonmail.android": "proton-mail",
    }

    @staticmethod
    def get_package_name(app: str) -> str:
        """The function `get_package_name` takes an app name as input and returns the corresponding package name.

        Parameters
        ----------
        app : str
            The `app` parameter is a string that represents the name of an app.

        Returns
        -------
            a string, which is the package name corresponding to the given app name.
        """
        for package, app_name in Patches.revanced_package_names.items():
            if app_name.upper() == app.upper():
                return package
        msg = f"App {app} not supported officially yet. Please provide package name in env to proceed."
        raise AppNotFoundError(msg)

    @staticmethod
    def support_app() -> dict[str, str]:
        """The function returns a dictionary of supported app IDs.

        Returns
        -------
            a dictionary of supported apps.
        """
        return Patches.revanced_package_names

    def fetch_patches(self: Self, config: RevancedConfig, app: APP) -> None:
        """The function fetches patches from a JSON file.

        Parameters
        ----------
        config : RevancedConfig
            The `config` parameter is of type `RevancedConfig` and represents the configuration for the
        application.
        app : APP
            The `app` parameter is of type `APP`. It represents an instance of the `APP` class.
        """
        self.patches_dict[app.app_name] = []
        patches = convert_command_output_to_json(
            f"{config.temp_folder}/{app.resource["cli"]["file_name"]}",
            f"{config.temp_folder}/{app.resource["patches"]["file_name"]}",
        )

        for patch in patches:
            if not patch["compatiblePackages"]:
                p = {x: patch[x] for x in ["name", "description"]}
                p["app"] = "universal"
                p["version"] = "all"
                self.patches_dict["universal_patch"].append(p)
            else:
                for compatible_package, version in [(x["name"], x["versions"]) for x in patch["compatiblePackages"]]:
                    if app.package_name == compatible_package:
                        p = {x: patch[x] for x in ["name", "description"]}
                        p["app"] = compatible_package
                        p["version"] = version[-1] if version else "all"
                        self.patches_dict[app.app_name].append(p)

        app.no_of_patches = len(self.patches_dict[app.app_name])

    def __init__(self: Self, config: RevancedConfig, app: APP) -> None:
        self.patches_dict: dict[str, list[dict[str, str]]] = {"universal_patch": []}
        self.fetch_patches(config, app)

    def get(self: Self, app: str) -> tuple[list[dict[str, str]], str]:
        """The function `get` returns all patches and version for a given application.

        Parameters
        ----------
        app : str
            The `app` parameter is a string that represents the name of the application for which you want
        to retrieve patches.

        Returns
        -------
            a tuple containing two elements. The first element is a list of dictionaries representing
        patches for the given app. The second element is a string representing the version of the
        patches.
        """
        patches = self.patches_dict[app]
        version = "latest"
        with contextlib.suppress(StopIteration):
            version = next(i["version"] for i in patches if i["version"] != "all")
        return patches, version

    def get_app_configs(self: Self, app: "APP") -> list[dict[str, str]]:
        """The function `get_app_configs` returns configurations for a given app.

        Parameters
        ----------
        app : "APP"
            The "app" parameter is the name of the application for which you want to get the
        configurations.

        Returns
        -------
            the total_patches, which is a list of dictionaries containing information about the patches for
        the given app. Each dictionary in the list contains the keys "Patches", "Version", and
        "Experimental".
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
        app.app_version = recommended_version
        app.experiment = experiment
        return total_patches
