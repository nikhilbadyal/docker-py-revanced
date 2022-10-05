import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import PriorityQueue
from time import perf_counter
from typing import Any, Tuple

import requests
from environs import Env
from loguru import logger
from requests import Session
from selectolax.lexbor import LexborHTMLParser
from tqdm import tqdm


class Downloader(object):
    def __init__(self, env: Env):
        self._CHUNK_SIZE = 2**21 * 5
        self._QUEUE: PriorityQueue[Tuple[float, str]] = PriorityQueue()
        self._QUEUE_LENGTH = 0
        self.temp_folder = Path("apks")

        self.session = Session()
        self.session.headers["User-Agent"] = "anything"
        self.build_extended = env.bool("BUILD_EXTENDED", False)
        self.apk_mirror = "https://www.apkmirror.com"
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
        self.upto_down = ["spotify"]
        self.download_revanced()

    def _download(self, url: str, file_name: str) -> None:
        logger.debug(f"Trying to download {file_name} from {url}")
        self._QUEUE_LENGTH += 1
        start = perf_counter()
        resp = self.session.get(url, stream=True)
        total = int(resp.headers.get("content-length", 0))
        bar = tqdm(
            desc=file_name,
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            colour="green",
        )
        with self.temp_folder.joinpath(file_name).open("wb") as dl_file, bar:
            for chunk in resp.iter_content(self._CHUNK_SIZE):
                size = dl_file.write(chunk)
                bar.update(size)
        self._QUEUE.put((perf_counter() - start, file_name))
        logger.debug(f"Downloaded {file_name}")

    def extract_download_link(self, page: str, app: str) -> None:
        logger.debug(f"Extracting download link from\n{page}")
        parser = LexborHTMLParser(self.session.get(page).text)

        resp = self.session.get(
            self.apk_mirror + parser.css_first("a.accent_bg").attributes["href"]
        )
        parser = LexborHTMLParser(resp.text)

        href = parser.css_first(
            "p.notes:nth-child(3) > span:nth-child(1) > a:nth-child(1)"
        ).attributes["href"]
        self._download(self.apk_mirror + href, f"{app}.apk")
        logger.debug("Finished Extracting link and downloading")

    def get_download_page(self, parser: LexborHTMLParser, main_page: str) -> str:
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
        download_url = self.apk_mirror + sub_url
        return download_url

    def __upto_down_downloader(self, app: str) -> Any:
        page = "https://spotify.en.uptodown.com/android/download"
        parser = LexborHTMLParser(self.session.get(page).text)
        main_page = parser.css_first("#detail-download-button")
        download_url = main_page.attributes["data-url"]
        app_version = parser.css_first(".version").text()
        self._download(download_url, "spotify.apk")
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version in rt")
        return app_version

    def apkmirror_specific_version(self, app: str, version: str) -> str:
        logger.debug(f"Trying to download {app},specific version {version}")
        version = version.replace(".", "-")
        main_page = f"{self.apk_mirror_version_urls.get(app)}-{version}-release/"
        parser = LexborHTMLParser(self.session.get(main_page).text)
        download_page = self.get_download_page(parser, main_page)
        self.extract_download_link(download_page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version")
        return version

    def apkmirror_latest_version(self, app: str) -> Any:
        logger.debug(f"Trying to download {app}'s latest version from apkmirror")
        page = self.apk_mirror_urls.get(app)
        if not page:
            logger.debug("Invalid app")
            sys.exit(1)
        parser = LexborHTMLParser(self.session.get(page).text)
        main_page = parser.css_first(".appRowVariantTag>.accent_color").attributes[
            "href"
        ]
        match = re.search(r"\d", main_page)
        if not match:
            logger.error("Cannot find app main page")
            sys.exit(-1)
        int_version = match.start()
        extra_release = main_page.rfind("release") - 1
        version = main_page[int_version:extra_release]
        version = version.replace("-", ".")
        main_page = f"{self.apk_mirror}{main_page}"
        parser = LexborHTMLParser(self.session.get(main_page).text)
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
        assets = [
            ["revanced", "revanced-cli", self.normal_cli_jar],
            ["revanced", "revanced-integrations", self.normal_integrations_apk],
            ["revanced", "revanced-patches", self.normal_patches_jar],
            ["inotia00", "VancedMicroG", "VancedMicroG.apk"],
        ]
        if self.build_extended:
            assets += [
                ["inotia00", "revanced-cli", self.cli_jar],
                ["inotia00", "revanced-integrations", self.integrations_apk],
                ["inotia00", "revanced-patches", self.patches_jar],
            ]
        with ThreadPoolExecutor(7) as executor:
            executor.map(lambda repo: self.repository(*repo), assets)
        logger.info("Downloaded revanced microG ,cli, integrations and patches.")

    def upto_down_downloader(self, app: str) -> Any:
        return self.__upto_down_downloader(app)

    def download_from_apkmirror(self, version: str, app: str) -> Any:
        if version and version != "latest":
            return self.apkmirror_specific_version(app, version)
        else:
            return self.apkmirror_latest_version(app)

    def download_apk_to_patch(self, version: str, app: str) -> Any:
        if app in self.upto_down:
            return self.upto_down_downloader(app)
        else:
            return self.download_from_apkmirror(version, app)
