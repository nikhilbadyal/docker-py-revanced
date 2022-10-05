from subprocess import PIPE, Popen
from time import perf_counter
from typing import Any, List

from environs import Env
from loguru import logger

from src.downloader import temp_folder

env = Env()


class ArgParser(object):
    build_extended = env.bool("BUILD_EXTENDED", False)
    extended_apps = ["youtube", "youtube_music"]
    keystore_name = env.str("KEYSTORE_FILE_NAME", "revanced.keystore")
    apk_mirror = "https://www.apkmirror.com"
    github = "https://www.github.com"
    normal_cli_jar = "revanced-cli.jar"
    normal_patches_jar = "revanced-patches.jar"
    normal_integrations_apk = "revanced-integrations.apk"
    cli_jar = f"inotia00-{normal_cli_jar}" if build_extended else normal_cli_jar
    patches_jar = (
        f"inotia00-{normal_patches_jar}" if build_extended else normal_patches_jar
    )
    integrations_apk = (
        f"inotia00-{normal_integrations_apk}"
        if build_extended
        else normal_integrations_apk
    )
    apk_mirror_urls = {
        "reddit": f"{apk_mirror}/apk/redditinc/reddit/",
        "twitter": f"{apk_mirror}/apk/twitter-inc/twitter/",
        "tiktok": f"{apk_mirror}/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/",
        "warnwetter": f"{apk_mirror}/apk/deutscher-wetterdienst/warnwetter/",
        "youtube": f"{apk_mirror}/apk/google-inc/youtube/",
        "youtube_music": f"{apk_mirror}/apk/google-inc/youtube-music/",
    }
    apk_mirror_version_urls = {
        "reddit": f"{apk_mirror_urls.get('reddit')}reddit",
        "twitter": f"{apk_mirror_urls.get('twitter')}twitter",
        "tiktok": f"{apk_mirror_urls.get('tiktok')}tik-tok-including-musical-ly",
        "warnwetter": f"{apk_mirror_urls.get('warnwetter')}warnwetter",
        "youtube": f"{apk_mirror_urls.get('youtube')}youtube",
        "youtube_music": f"{apk_mirror_urls.get('youtube_music')}youtube-music",
    }
    upto_down = ["spotify"]

    def __init__(self, patcher):
        self._PATCHES = []
        self._EXCLUDED = []
        self.patcher = patcher
        self.keystore_name = env.str("KEYSTORE_FILE_NAME", "revanced.keystore")

    def include(self, name: str) -> None:
        self._PATCHES.extend(["-i", name])

    def exclude(self, name: str) -> None:
        self._PATCHES.extend(["-e", name])
        self._EXCLUDED.append(name)

    def get_excluded_patches(self) -> List[Any]:
        return self._EXCLUDED

    def run(self, app: str, version: str, is_experimental: bool = False) -> None:
        logger.debug(f"Sending request to revanced cli for building {app} revanced")
        cli = self.normal_cli_jar
        patches = self.normal_patches_jar
        integrations = self.normal_integrations_apk
        if self.build_extended and app in self.extended_apps:
            cli = self.cli_jar
            patches = self.patches_jar
            integrations = self.integrations_apk
        args = [
            "-jar",
            cli,
            "-a",
            app + ".apk",
            "-b",
            patches,
            "-m",
            integrations,
            "-o",
            f"Re-{app}-{version}-output.apk",
            "--keystore",
            self.keystore_name,
        ]
        if is_experimental:
            logger.debug("Using experimental features")
            args.append("--experimental")
        args[1::2] = map(lambda i: temp_folder.joinpath(i), args[1::2])

        if self._PATCHES:
            args.extend(self._PATCHES)

        start = perf_counter()
        process = Popen(["java", *args], stdout=PIPE)
        for line in process.stdout:
            logger.debug(line.decode(), flush=True, end="")
        process.wait()
        logger.debug(
            f"Patching completed for app {app} in {perf_counter() - start:.2f} "
            f"seconds."
        )
