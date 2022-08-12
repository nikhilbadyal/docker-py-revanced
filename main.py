import subprocess
import sys
from atexit import register
from pathlib import Path
from queue import PriorityQueue
from shutil import rmtree
from subprocess import PIPE, Popen
from time import perf_counter
from typing import Dict, List, Tuple

from loguru import logger
from requests import Session
from selectolax.lexbor import LexborHTMLParser
from tqdm import tqdm

temp_folder = Path("apks")
session = Session()
session.headers["User-Agent"] = "anything"
apps = ["youtube", "youtube-music", "twitter", "reddit"]
apk_mirror = "https://www.apkmirror.com"


class Downloader:
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
        with temp_folder.joinpath(file_name).open("wb") as dl_file, tqdm(
            desc=file_name,
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            colour="green",
        ) as bar:
            for chunk in resp.iter_content(cls._CHUNK_SIZE):
                size = dl_file.write(chunk)
                bar.update(size)
        cls._QUEUE.put((perf_counter() - start, file_name))
        logger.debug(f"Downloaded {file_name}")

    @classmethod
    def extract_download_link(cls, page: str, app: str):
        logger.debug(f"Extracting download link from {page}")
        parser = LexborHTMLParser(session.get(page).text)

        resp = session.get(
            apk_mirror + parser.css_first("a.accent_bg").attributes["href"]
        )
        parser = LexborHTMLParser(resp.text)

        href = parser.css_first(
            "p.notes:nth-child(3) > span:nth-child(1) > a:nth-child(1)"
        ).attributes["href"]
        cls._download(apk_mirror + href, f"{app}.apk")
        logger.debug(f"Finished Extracting and download link from {page}")

    @classmethod
    def apkmirror(cls, app: str, version: str) -> None:
        logger.debug(f"Trying to download {app} apk from apkmirror")
        version = "-".join(
            v.zfill(2 if i else 0) for i, v in enumerate(version.split("."))
        )
        logger.debug(f"Version for {app} to download  from apkmirror is {version}")
        page = f"""
        {apk_mirror}/apk/google-inc/
        {app}/{app}-{version}-release/{app}-{version}-android-apk-download/
        """
        cls.extract_download_link(page, app)

    @classmethod
    def find_second_last(cls, text: str, pattern: str) -> int:
        return text.rfind(pattern, 0, text.rfind(pattern))

    @classmethod
    def apkmirror_reddit_twitter(cls, app: str, version: str) -> None:
        logger.debug(f"Trying to download {app} apk from apkmirror in rt")
        if app == "reddit":
            page = f"{apk_mirror}/apk/redditinc/reddit/"
        elif app == "twitter":
            page = f"{apk_mirror}/apk/twitter-inc/twitter/"
        else:
            logger.debug("Invalid app")
            sys.exit(1)
        parser = LexborHTMLParser(session.get(page).text)
        suburl = parser.css_first("a.downloadLink").attributes["href"]
        last2 = cls.find_second_last(suburl, "/")
        version_url = suburl[last2:]
        minus_occurance = version_url.rfind("-")
        version_url = version_url[:minus_occurance]
        download_url = version_url + "-2-android-apk-download/"
        url = apk_mirror + suburl + download_url[1:]
        page = url
        cls.extract_download_link(page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror in rt")

    @classmethod
    def repository(cls, name: str) -> None:
        logger.debug(f"Trying to download {name} from github")
        resp = session.get(
            f"https://github.com/revanced/revanced-{name}/releases/latest"
        )
        parser = LexborHTMLParser(resp.text)
        url = parser.css("li.Box-row > div:nth-child(1) > a:nth-child(2)")[:-2][
            -1
        ].attributes["href"]
        cls._download("https://github.com" + url, Path(url).with_stem(name).name)

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


class Patches:
    def __init__(self) -> None:
        logger.debug("fetching all patches")
        resp = session.get(
            "https://raw.githubusercontent.com/revanced/revanced-patches/main/README.md"
        )
        available_patches = []
        for app in resp.text.split("### 📦 ")[1:]:
            lines = app.splitlines()

            app_name = lines[0][1:-1]
            app_patches = []
            for line in lines:
                patch = line.split("|")[1:-1]
                if len(patch) == 3:
                    (n, d, v), a = [i.replace("`", "").strip() for i in patch], app_name
                    app_patches.append((n, d, a, v))

            available_patches.extend(app_patches[2:])

        youtube, music, twitter, reddit = [], [], [], []
        for n, d, a, v in available_patches:
            patch = {"name": n, "description": d, "app": a, "version": v}
            if "twitter" in a:
                twitter.append(patch)
            elif "reddit" in a:
                reddit.append(patch)
            elif "music" in a:
                music.append(patch)
            elif "youtube" in a:
                youtube.append(patch)
        self._yt = youtube
        self._ytm = music
        self._twitter = twitter
        self._reddit = reddit
        logger.debug(f"Total patches in youtube are {len(youtube)}")
        logger.debug(f"Total patches in youtube-music are {len(music)}")
        logger.debug(f"Total patches in twitter are {len(twitter)}")
        logger.debug(f"Total patches in reddit are {len(reddit)}")

    def get(self, app: str) -> Tuple[List[Dict[str, str]], str]:
        logger.debug("Getting patches for %s" % app)
        if "twitter" == app:
            patches = self._twitter
        elif "reddit" == app:
            patches = self._reddit
        elif "youtube-music" == app:
            patches = self._ytm
        elif "youtube" == app:
            patches = self._yt
        else:
            logger.debug("Invalid app name")
            sys.exit(-1)
        version = ""
        if app in ("youtube", "youtube-music"):
            version = next(i["version"] for i in patches if i["version"] != "all")
            logger.debug("Version for app is  %s" % version)
        else:
            logger.debug("Empty version because it's not youtube or youtube-music")
        return patches, version


class ArgParser:
    _PATCHES = []

    @classmethod
    def include(cls, name: str) -> None:
        cls._PATCHES.extend(["-i", name])

    @classmethod
    def exclude(cls, name: str) -> None:
        cls._PATCHES.extend(["-e", name])

    @classmethod
    def run(cls, app: str) -> None:
        logger.debug(f"Sending request to revanced cli for building {app} revanced")
        args = [
            "-jar",
            "cli.jar",
            "-a",
            app + ".apk",
            "-b",
            "patches.jar",
            "-m",
            "integrations.apk",
            "-o",
            f"{app}-output.apk",
        ]
        if app == "reddit":
            args.append("-r")
            args.remove("-m")
            args.remove("integrations.apk")

        args[1::2] = map(lambda i: temp_folder.joinpath(i), args[1::2])

        if cls._PATCHES:
            args.extend(cls._PATCHES)

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


def main() -> None:
    patches = pre_requisite()
    downloader = Downloader
    downloader.repository("cli")
    downloader.repository("integrations")
    downloader.repository("patches")
    # downloader.report()

    def get_patches() -> None:
        logger.debug(f"Excluding patches for app {app}")
        selected_patches = list(range(0, len(app_patches)))
        if app == "youtube":
            selected_patches.remove(9)
        for i, v in enumerate(app_patches):
            arg_parser.include(
                v["name"]
            ) if i in selected_patches else arg_parser.exclude(v["name"])
        logger.debug(f"Excluded patches for app {app}")

    for app in apps:
        try:
            arg_parser = ArgParser
            logger.debug("Trying to build %s" % app)
            app_patches, version = patches.get(app=app)
            if app == "reddit" or app == "twitter":
                downloader.apkmirror_reddit_twitter(app, version)
            else:
                downloader.apkmirror(app, version)
            get_patches()
            # downloader.report()
            logger.debug(f"Download completed {app}")
            arg_parser.run(app=app)
        except Exception as e:
            logger.debug(f"Failed to build {app} because of {e}")
            sys.exit(-1)


if __name__ == "__main__":
    main()
