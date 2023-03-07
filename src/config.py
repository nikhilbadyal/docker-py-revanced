"""Revanced Configurations."""
from pathlib import Path
from typing import Dict, List

from environs import Env
from requests import Session

from src.utils import all_builds, default_build


class RevancedConfig:
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
        ]
        self.apk_pure = ["hex-editor"]
        self.apk_sos = ["expensemanager"]
        self.keystore_name = env.str("KEYSTORE_FILE_NAME", "revanced.keystore")
        self.ci_test = env.bool("CI_TEST", False)
        self.apps = env.list(
            "PATCH_APPS", all_builds if self.ci_test else default_build
        )
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
            "citra": f"{self.apk_mirror}/apk/citra-emulator/citra-emulator/",
            "icon_pack_studio": f"{self.apk_mirror}/apk/smart-launcher-team/icon-pack-studio/",
            "twitch": f"{self.apk_mirror}/apk/twitch-interactive-inc/twitch/",
            "windy": f"{self.apk_mirror}/apk/windy-weather-world-inc/windy-wind-weather-forecast/",
            "tasker": f"{self.apk_mirror}/apk/joaomgcd/tasker-crafty-apps-eu/",
        }
        self.apk_mirror_version_urls = {
            "reddit": f"{self.apk_mirror_urls.get('reddit')}reddit",
            "twitter": f"{self.apk_mirror_urls.get('twitter')}twitter",
            "tiktok": f"{self.apk_mirror_urls.get('tiktok')}tik-tok-including-musical-ly",
            "warnwetter": f"{self.apk_mirror_urls.get('warnwetter')}warnwetter",
            "youtube": f"{self.apk_mirror_urls.get('youtube')}youtube",
            "youtube_music": f"{self.apk_mirror_urls.get('youtube_music')}youtube-music",
            "ticktick": f"{self.apk_mirror_urls.get('ticktick')}ticktick-to-do-list-with-reminder-day-planner",
            "citra": f"{self.apk_mirror_urls.get('citra')}citra-emulator",
            "icon_pack_studio": f"{self.apk_mirror_urls.get('icon_pack_studio')}icon-pack-studio",
            "twitch": f"{self.apk_mirror_urls.get('twitch')}twitch",
            "windy": f"{self.apk_mirror_urls.get('windy')}windy-wind-weather-forecast",
            "tasker": f"{self.apk_mirror_urls.get('tasker')}tasker-crafty-apps-eu/",
        }
        self.archs_to_build = env.list("ARCHS_TO_BUILD", [])
        self.alternative_youtube_patches = env.list("ALTERNATIVE_YOUTUBE_PATCHES", [])
        self.alternative_youtube_music_patches = env.list(
            "ALTERNATIVE_YOUTUBE_MUSIC_PATCHES", []
        )
        self.existing_downloaded_apks = env.list("EXISTING_DOWNLOADED_APKS", [])
        self.personal_access_token = env.str("PERSONAL_ACCESS_TOKEN", None)
