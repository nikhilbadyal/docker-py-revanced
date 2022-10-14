"""Revanced Configurations."""
from pathlib import Path
from typing import List

from environs import Env
from requests import Session

from src.utils import supported_apps


class RevancedConfig:
    """Revanced Configurations."""

    def __init__(self, env: Env) -> None:
        self.env = env
        self.temp_folder = Path("apks")
        self.session = Session()
        self.session.headers["User-Agent"] = "anything"
        self.build_extended = env.bool("BUILD_EXTENDED", False)
        self.apk_mirror = "https://www.apkmirror.com"
        self.upto_down = ["spotify"]
        self.keystore_name = env.str("KEYSTORE_FILE_NAME", "revanced.keystore")
        self.apps = env.list("PATCH_APPS", supported_apps)
        self.extended_apps: List[str] = ["youtube", "youtube_music"]
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
        }
        self.apk_mirror_version_urls = {
            "reddit": f"{self.apk_mirror_urls.get('reddit')}reddit",
            "twitter": f"{self.apk_mirror_urls.get('twitter')}twitter",
            "tiktok": f"{self.apk_mirror_urls.get('tiktok')}tik-tok-including-musical-ly",
            "warnwetter": f"{self.apk_mirror_urls.get('warnwetter')}warnwetter",
            "youtube": f"{self.apk_mirror_urls.get('youtube')}youtube",
            "youtube_music": f"{self.apk_mirror_urls.get('youtube_music')}youtube-music",
        }
        self.build_og_nd_branding_youtube = env.bool("BUILD_OG_BRANDING_YOUTUBE", False)
