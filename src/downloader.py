import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import PriorityQueue
from time import perf_counter
from typing import Tuple

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
    def __init__(self):
        self._CHUNK_SIZE = 2**21 * 5
        self._QUEUE: PriorityQueue[Tuple] = PriorityQueue()
        self._QUEUE_LENGTH = 0

    def _download(self, url: str, file_name: str) -> None:
        logger.debug(f"Trying to download {file_name} from {url}")
        self._QUEUE_LENGTH += 1
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
            for chunk in resp.iter_content(self._CHUNK_SIZE):
                size = dl_file.write(chunk)
                bar.update(size)
        self._QUEUE.put((perf_counter() - start, file_name))
        logger.debug(f"Downloaded {file_name}")

    def extract_download_link(self, page: str, app: str):
        logger.debug(f"Extracting download link from\n{page}")
        parser = LexborHTMLParser(session.get(page).text)

        resp = session.get(
            apk_mirror + parser.css_first("a.accent_bg").attributes["href"]
        )
        parser = LexborHTMLParser(resp.text)

        href = parser.css_first(
            "p.notes:nth-child(3) > span:nth-child(1) > a:nth-child(1)"
        ).attributes["href"]
        self._download(apk_mirror + href, f"{app}.apk")
        logger.debug("Finished Extracting link and downloading")

    def get_download_page(self, parser, main_page):
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

    def __upto_down_downloader(self, app: str) -> str:
        page = "https://spotify.en.uptodown.com/android/download"
        parser = LexborHTMLParser(session.get(page).text)
        main_page = parser.css_first("#detail-download-button")
        download_url = main_page.attributes["data-url"]
        app_version = parser.css_first(".version").text()
        self._download(download_url, "spotify.apk")
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version in rt")
        return app_version

    def apkmirror_specific_version(self, app: str, version: str) -> str:
        logger.debug(f"Trying to download {app},specific version {version}")
        version = version.replace(".", "-")
        main_page = f"{apk_mirror_version_urls.get(app)}-{version}-release/"
        parser = LexborHTMLParser(session.get(main_page).text)
        download_page = self.get_download_page(parser, main_page)
        self.extract_download_link(download_page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version")
        return version

    def apkmirror_latest_version(self, app: str) -> str:
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
        download_page = self.get_download_page(parser, main_page)
        self.extract_download_link(download_page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version in rt")
        return version

    def repository(self, owner: str, name: str, file_name: str) -> None:
        logger.debug(f"Trying to download {name} from github")
        repo_url = f"https://api.github.com/repos/{owner}/{name}/releases/latest"
        r = requests.get(
            repo_url, headers={"Content-Type": "application/vnd.github.v3+json"}
        )
        if name == "revanced-patches":
            download_url = r.json()["assets"][1]["browser_download_url"]
        else:
            download_url = r.json()["assets"][0]["browser_download_url"]
        self._download(download_url, file_name=file_name)

    def download_revanced(self) -> None:
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
            executor.map(lambda repo: self.repository(*repo), assets)
        logger.info("Downloaded revanced microG ,cli, integrations and patches.")

    def upto_down_downloader(self, app: str) -> str:
        return self.__upto_down_downloader(app)

    def download_from_apkmirror(self, version: str, app: str) -> str:
        if version and version != "latest":
            return self.apkmirror_specific_version(app, version)
        else:
            return self.apkmirror_latest_version(app)

    def download_apk_to_patch(self, version: str, app: str) -> str:
        if app in upto_down:
            return self.upto_down_downloader(app)
        else:
            return self.download_from_apkmirror(version, app)
