import asyncio  # noqa: D100
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from loguru import logger

sys.path.append(str(Path.cwd()))
from src.browser.site import source as page_source


async def main() -> None:  # noqa: D103
    # display = Display(visible=False, size=(800, 600))  # noqa: ERA001
    # display.start()  # noqa: ERA001
    # logger.info("Started display")  # noqa: ERA001

    url = "https://www.wikipedia.com/"  ## Redirect test
    url = "https://nowsecure.nl"  ## Cloudflare
    url = "https://bot.sannysoft.com/"  ## AntiBot validator
    url = "https://fingerprintjs.github.io/BotD"  ## AntiBot validator
    url = "https://community.cloudflare.com/t/bot-traffic-managed-to-bypass-cloudflare-interactive-challenge-captcha/541364"  ## Cloudflare  # noqa: E501
    url = "https://nopecha.com/demo"  ## Cloudflare

    try:
        r = await page_source(url)
        soup = BeautifulSoup(r.text, "html.parser")
        element = soup.select_one("title")
        if element:
            print(element.text)  # noqa: T201
    except Exception as e:  # noqa: BLE001
        logger.error(e)

    # display.stop()  # noqa: ERA001


async def _looper() -> None:
    for _ in range(1):
        await main()


if __name__ == "__main__":
    start = time.perf_counter()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_looper())
    stop = time.perf_counter()
    print("Elapsed time during the whole program in seconds:", stop - start)  # noqa: T201
