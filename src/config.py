"""Revanced Configurations."""
from pathlib import Path
from typing import Dict, List

from environs import Env
from requests import Session

from src.utils import default_build


class RevancedConfig(object):
    """Revanced Configurations."""

    def __init__(self, env: Env) -> None:
        self.app_versions: Dict[str, str] = {}
        self.env = env
        self.temp_folder = Path("apks")
        self.session = Session()
        self.session.headers["User-Agent"] = "anything"
        self.build_extended = env.bool("BUILD_EXTENDED", False)
        self.apk_mirror = "https://www.apkmirror.com"
        self.upto_down = [
            "spotify",
            "nyx-music-player",
            "my-expenses",
            "backdrops",
            "twitch",
            "irplus",
            "meme-generator-free",
            "yuka",
            "facebook",
        ]
        self.apk_pure = ["hex-editor", "androidtwelvewidgets"]
        self.apk_sos = ["expensemanager", "candyvpn"]
        self.keystore_name = env.str("KEYSTORE_FILE_NAME", "revanced.keystore")
        self.ci_test = env.bool("CI_TEST", False)
        self.apps = env.list("PATCH_APPS", default_build)
        self.extended_apps: List[str] = ["youtube", "youtube_music"]
        self.rip_libs_apps: List[str] = ["youtube"]
        self.normal_cli_jar = "revanced-cli.jar"
        self.normal_patches_jar = "revanced-patches.jar"
        self.normal_integrations_apk = "revanced-integrations.apk"
        self.cli_jar = (
            f"inotia00-{self.normal_cli_jar}"
            if self.build_extended
            else self.normal_cli_jar
        )
        self.patches_jar = (
            f"inotia00-{self.normal_patches_jar}"
            if self.build_extended
            else self.normal_patches_jar
        )
        self.integrations_apk = (
            f"inotia00-{self.normal_integrations_apk}"
            if self.build_extended
            else self.normal_integrations_apk
        )
        self.apk_mirror_urls = {
            "reddit": f"{self.apk_mirror}/apk/redditinc/reddit/",
            "twitter": f"{self.apk_mirror}/apk/twitter-inc/twitter/",
            "tiktok": f"{self.apk_mirror}/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/",
            "warnwetter": f"{self.apk_mirror}/apk/deutscher-wetterdienst/warnwetter/",
            "youtube": f"{self.apk_mirror}/apk/google-inc/youtube/",
            "youtube_music": f"{self.apk_mirror}/apk/google-inc/youtube-music/",
            "ticktick": f"{self.apk_mirror}/apk/appest-inc/ticktick-to-do-list-with-reminder-day-planner/",
            "icon_pack_studio": f"{self.apk_mirror}/apk/smart-launcher-team/icon-pack-studio/",
            "twitch": f"{self.apk_mirror}/apk/twitch-interactive-inc/twitch/",
            "windy": f"{self.apk_mirror}/apk/windy-weather-world-inc/windy-wind-weather-forecast/",
            "tasker": f"{self.apk_mirror}/apk/joaomgcd/tasker-crafty-apps-eu/",
            "vsco": f"{self.apk_mirror}/apk/vsco/vsco-cam/",
            "nova_launcher": f"{self.apk_mirror}/apk/teslacoil-software/nova-launcher/",
            "netguard": f"{self.apk_mirror}/apk/marcel-bokhorst/netguard-no-root-firewall/",
            "instagram": f"{self.apk_mirror}/apk/instagram/instagram-instagram/",
            "inshorts": f"{self.apk_mirror}/apk/inshorts-formerly-news-in-shorts/",
            "facebook": f"{self.apk_mirror}/apk/facebook-2/facebook/",
            "grecorder": f"{self.apk_mirror}/apk/google-inc/google-recorder/",
            "trakt": f"{self.apk_mirror}/apk/trakt/trakt/",
            "candyvpn": f"{self.apk_mirror}/apk/liondev-io/candylink-vpn/",
            "sonyheadphone": f"{self.apk_mirror}/apk/sony-corporation/sony-headphones-connect/",
        }
        self.apk_mirror_version_urls = {
            key: value + value.split("/")[-2]
            for key, value in self.apk_mirror_urls.items()
        }
        self.archs_to_build = env.list("ARCHS_TO_BUILD", [])
        self.alternative_youtube_patches = env.list("ALTERNATIVE_YOUTUBE_PATCHES", [])
        self.alternative_youtube_music_patches = env.list(
            "ALTERNATIVE_YOUTUBE_MUSIC_PATCHES", []
        )
        self.existing_downloaded_apks = env.list("EXISTING_DOWNLOADED_APKS", [])
        self.personal_access_token = env.str("PERSONAL_ACCESS_TOKEN", None)
