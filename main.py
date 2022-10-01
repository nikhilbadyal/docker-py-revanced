import re
import subprocess
import sys
from atexit import register
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import PriorityQueue
from shutil import rmtree
from subprocess import PIPE, Popen
from time import perf_counter
from typing import Any, Dict, List, Tuple, Type

import requests
from environs import Env
from loguru import logger
from requests import Session
from selectolax.lexbor import LexborHTMLParser
from tqdm import tqdm

env = Env()
temp_folder = Path("apks")
session = Session()
session.headers["User-Agent"] = "anything"
supported_apps = [
    "youtube",
    "youtube_music",
    "twitter",
    "reddit",
    "tiktok",
    "warnwetter",
    "spotify",
]
apps = env.list("PATCH_APPS", supported_apps)
build_extended = env.bool("BUILD_EXTENDED", False)
extended_apps = ["youtube", "youtube_music"]
keystore_name = env.str("KEYSTORE_FILE_NAME", "revanced.keystore")
apk_mirror = "https://www.apkmirror.com"
github = "https://www.github.com"
normal_cli_jar = "revanced-cli.jar"
normal_patches_jar = "revanced-patches.jar"
normal_integrations_apk = "revanced-integrations.apk"
cli_jar = f"inotia00-{normal_cli_jar}" if build_extended else normal_cli_jar
patches_jar = f"inotia00-{normal_patches_jar}" if build_extended else normal_patches_jar
integrations_apk = (
    f"inotia00-{normal_integrations_apk}" if build_extended else normal_integrations_apk
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


class Downloader(object):
    _CHUNK_SIZE = 2**21 * 5
    _QUEUE = PriorityQueue()
    _QUEUE_LENGTH = 0

    @classmethod
    def _download(cls, url: str, file_name: str) -> None:
        logger.debug(f"Trying to download {file_name} from {url}")
        cls._QUEUE_LENGTH += 1
        start = perf_counter()
        resp = session.get(url, stream=True)
        total = int(resp.headers.get("content-length", 0))
        bar = tqdm(
            desc=file_name,
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            colour="green",
        )
        with temp_folder.joinpath(file_name).open("wb") as dl_file, bar:
            for chunk in resp.iter_content(cls._CHUNK_SIZE):
                size = dl_file.write(chunk)
                bar.update(size)
        cls._QUEUE.put((perf_counter() - start, file_name))
        logger.debug(f"Downloaded {file_name}")

    @classmethod
    def extract_download_link(cls, page: str, app: str):
        logger.debug(f"Extracting download link from\n{page}")
        parser = LexborHTMLParser(session.get(page).text)

        resp = session.get(
            apk_mirror + parser.css_first("a.accent_bg").attributes["href"]
        )
        parser = LexborHTMLParser(resp.text)

        href = parser.css_first(
            "p.notes:nth-child(3) > span:nth-child(1) > a:nth-child(1)"
        ).attributes["href"]
        cls._download(apk_mirror + href, f"{app}.apk")
        logger.debug("Finished Extracting link and downloading")

    @classmethod
    def get_download_page(cls, parser, main_page):
        apm = parser.css(".apkm-badge")
        sub_url = ""
        for is_apm in apm:
            if "APK" in is_apm.text():
                parser = is_apm.parent
                sub_url = parser.css_first(".accent_color").attributes["href"]
                break
        if sub_url == "":
            logger.exception(
                f"Unable to find any apk on apkmirror_specific_version on {main_page}"
            )
            sys.exit(-1)
        download_url = apk_mirror + sub_url
        return download_url

    @classmethod
    def upto_down_downloader(cls, app: str) -> str:
        page = "https://spotify.en.uptodown.com/android/download"
        parser = LexborHTMLParser(session.get(page).text)
        main_page = parser.css_first("#detail-download-button")
        download_url = main_page.attributes["data-url"]
        app_version = parser.css_first(".version").text()
        cls._download(download_url, "spotify.apk")
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version in rt")
        return app_version

    @classmethod
    def apkmirror_specific_version(cls, app: str, version: str) -> str:
        logger.debug(f"Trying to download {app},specific version {version}")
        version = version.replace(".", "-")
        main_page = f"{apk_mirror_version_urls.get(app)}-{version}-release/"
        parser = LexborHTMLParser(session.get(main_page).text)
        download_page = cls.get_download_page(parser, main_page)
        cls.extract_download_link(download_page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version")
        return version

    @classmethod
    def apkmirror_latest_version(cls, app: str) -> str:
        logger.debug(f"Trying to download {app}'s latest version from apkmirror")
        page = apk_mirror_urls.get(app)
        if not page:
            logger.debug("Invalid app")
            sys.exit(1)
        parser = LexborHTMLParser(session.get(page).text)
        main_page = parser.css_first(".appRowVariantTag>.accent_color").attributes[
            "href"
        ]
        int_version = re.search(r"\d", main_page).start()
        extra_release = main_page.rfind("release") - 1
        version = main_page[int_version:extra_release]
        version = version.replace("-", ".")
        main_page = f"{apk_mirror}{main_page}"
        parser = LexborHTMLParser(session.get(main_page).text)
        download_page = cls.get_download_page(parser, main_page)
        cls.extract_download_link(download_page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version in rt")
        return version

    @classmethod
    def repository(cls, owner: str, name: str, file_name: str) -> None:
        logger.debug(f"Trying to download {name} from github")
        repo_url = f"https://api.github.com/repos/{owner}/{name}/releases/latest"
        r = requests.get(
            repo_url, headers={"Content-Type": "application/vnd.github.v3+json"}
        )
        if name == "revanced-patches":
            download_url = r.json()["assets"][1]["browser_download_url"]
        else:
            download_url = r.json()["assets"][0]["browser_download_url"]
        cls._download(download_url, file_name=file_name)

    @classmethod
    def report(cls) -> None:
        started = False
        while True:
            item = cls._QUEUE.get()
            logger.debug(f"{item[1]} downloaded in {item[0]:.2f} seconds.")
            cls._QUEUE.task_done()
            cls._QUEUE_LENGTH -= 1

            if not started:
                started = True
            elif started and not cls._QUEUE_LENGTH:
                break


class Patches(object):
    def __init__(self) -> None:
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

        if build_extended:
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


class ArgParser(object):
    def __init__(self):
        self._PATCHES = []
        self._EXCLUDED = []

    def include(self, name: str) -> None:
        self._PATCHES.extend(["-i", name])

    def exclude(self, name: str) -> None:
        self._PATCHES.extend(["-e", name])
        self._EXCLUDED.append(name)

    def get_excluded_patches(self) -> List[Any]:
        return self._EXCLUDED

    def run(self, app: str, version: str, is_experimental: bool = False) -> None:
        logger.debug(f"Sending request to revanced cli for building {app} revanced")
        cli = normal_cli_jar
        patches = normal_patches_jar
        integrations = normal_integrations_apk
        if build_extended and app in extended_apps:
            cli = cli_jar
            patches = patches_jar
            integrations = integrations_apk
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
            keystore_name,
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


@register
def close() -> None:
    session.close()
    cache = Path("revanced-cache")
    if cache.is_dir():
        rmtree(cache)


def check_java() -> None:
    logger.debug("Checking if java is available")
    jd = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT)
    jd = str(jd)[1:-1]
    if "Runtime Environment" not in jd:
        logger.debug("Java Must be installed")
        exit(-1)
    if "17" not in jd:
        logger.debug("Java 17 Must be installed")
        exit(-1)
    logger.debug("Cool!! Java is available")


def pre_requisite():
    check_java()
    patches = Patches()
    return patches


def download_revanced(downloader: Type[Downloader]) -> None:
    assets = (
        ("revanced", "revanced-cli", normal_cli_jar),
        ("revanced", "revanced-integrations", normal_integrations_apk),
        ("revanced", "revanced-patches", normal_patches_jar),
        ("inotia00", "VancedMicroG", "VancedMicroG.apk"),
    )
    if build_extended:
        assets += (
            ("inotia00", "revanced-cli", cli_jar),
            ("inotia00", "revanced-integrations", integrations_apk),
            ("inotia00", "revanced-patches", patches_jar),
        )
    with ThreadPoolExecutor() as executor:
        executor.map(lambda repo: downloader.repository(*repo), assets)
    logger.info("Downloaded revanced microG ,cli, integrations and patches.")


def upto_down_downloader(app: str, downloader: Type[Downloader]) -> str:
    return downloader.upto_down_downloader(app)


def download_from_apkmirror(
    version: str, app: str, downloader: Type[Downloader]
) -> str:
    if version and version != "latest":
        return downloader.apkmirror_specific_version(app, version)
    else:
        return downloader.apkmirror_latest_version(app)


def download_apk_to_patch(version: str, app: str, downloader: Type[Downloader]) -> str:
    if app in upto_down:
        return upto_down_downloader(app, downloader)
    else:
        return download_from_apkmirror(version, app, downloader)


def main() -> None:
    patches = pre_requisite()
    downloader = Downloader
    download_revanced(downloader)

    def get_patches() -> None:
        logger.debug(f"Excluding patches for app {app}")
        if build_extended and app in extended_apps:
            excluded_patches = env.list(f"EXCLUDE_PATCH_{app}_EXTENDED".upper(), [])
        else:
            excluded_patches = env.list(f"EXCLUDE_PATCH_{app}".upper(), [])
        for patch in app_patches:
            arg_parser.include(patch["name"]) if patch[
                "name"
            ] not in excluded_patches else arg_parser.exclude(patch["name"])
        excluded = arg_parser.get_excluded_patches()
        if excluded:
            logger.debug(f"Excluded patches {excluded} for {app}")
        else:
            logger.debug(f"No excluded patches for {app}")

    def get_patches_version() -> Any:
        experiment = False
        total_patches, recommended_version = patches.get(app=app)
        env_version = env.str(f"{app}_VERSION".upper(), None)
        if env_version:
            logger.debug(f"Picked {app} version {env_version} from env.")
            if env_version == "latest" or env_version > recommended_version:
                experiment = True
            recommended_version = env_version
        return total_patches, recommended_version, experiment

    logger.info(f"Will Patch only {apps}")
    for app in apps:
        try:
            arg_parser = ArgParser()
            logger.debug("Trying to build %s" % app)
            app_patches, version, is_experimental = get_patches_version()
            version = download_apk_to_patch(version, app, downloader)
            get_patches()
            logger.debug(f"Downloaded {app}, version {version}")
            arg_parser.run(app=app, version=version, is_experimental=is_experimental)
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(-1)
