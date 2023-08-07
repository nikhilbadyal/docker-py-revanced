"""Revanced Configurations."""
from pathlib import Path
from typing import List

from environs import Env
from requests import Session

from src.utils import default_build

default_cli = "https://github.com/revanced/revanced-cli/releases/latest"
default_patches = "https://github.com/revanced/revanced-patches/releases/latest"
default_patches_json = default_patches
default_integrations = (
    "https://github.com/revanced/revanced-integrations/releases/latest"
)


class RevancedConfig(object):
    """Revanced Configurations."""

    def __init__(self, env: Env) -> None:
        self.env = env
        self.temp_folder = Path("apks")
        self.session = Session()
        self.session.headers["User-Agent"] = "anything"
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
        ]
        self.apk_pure = ["hex-editor", "androidtwelvewidgets"]
        self.apk_sos = ["expensemanager", "candyvpn"]
        self.ci_test = env.bool("CI_TEST", False)
        self.apps = env.list("PATCH_APPS", default_build)
        self.rip_libs_apps: List[str] = []
        self.apk_mirror_urls = {
            "reddit": f"{self.apk_mirror}/apk/redditinc/reddit/",
            "twitter": f"{self.apk_mirror}/apk/x-corp/twitter/",
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
            "messenger": f"{self.apk_mirror}/apk/facebook-2/messenger/",
            "grecorder": f"{self.apk_mirror}/apk/google-inc/google-recorder/",
            "trakt": f"{self.apk_mirror}/apk/trakt/trakt/",
            "candyvpn": f"{self.apk_mirror}/apk/liondev-io/candylink-vpn/",
            "sonyheadphone": f"{self.apk_mirror}/apk/sony-corporation/sony-headphones-connect/",
            "relay": f"{self.apk_mirror}/apk/dbrady/relay-for-reddit-2/",
            "boost": f"{self.apk_mirror}/apk/ruben-mayayo/boost-for-reddit/",
            "rif": f"{self.apk_mirror}/apk/talklittle/reddit-is-fun/",
            "sync": f"{self.apk_mirror}/apk/red-apps-ltd/sync-for-reddit/",
            "infinity": f"{self.apk_mirror}/apk/docile-alligator/infinity-for-reddit/",
            "slide": f"{self.apk_mirror}/apk/haptic-apps/slide-for-reddit/",
            "bacon": f"{self.apk_mirror}/apk/onelouder-apps/baconreader-for-reddit/",
            "pixiv": f"{self.apk_mirror}/apk/pixiv-inc/pixiv/",
        }
        self.apk_mirror_version_urls = {
            key: value + value.split("/")[-2]
            for key, value in self.apk_mirror_urls.items()
        }
        self.existing_downloaded_apks = env.list("EXISTING_DOWNLOADED_APKS", [])
        self.personal_access_token = env.str("PERSONAL_ACCESS_TOKEN", None)
        self.dry_run = env.bool("DRY_RUN", False)
        self.global_cli_dl = env.str("GLOBAL_CLI_DL", default_cli)
        self.global_patches_dl = env.str("GLOBAL_PATCHES_DL", default_patches)
        self.global_patches_json_dl = env.str(
            "GLOBAL_PATCHES_JSON_DL", default_patches_json
        )
        self.global_integrations_dl = env.str(
            "GLOBAL_INTEGRATIONS_DL", default_integrations
        )
        self.global_keystore_name = env.str(
            "GLOBAL_KEYSTORE_FILE_NAME", "revanced.keystore"
        )
        self.global_archs_to_build = env.list("GLOBAL_ARCHS_TO_BUILD", [])
