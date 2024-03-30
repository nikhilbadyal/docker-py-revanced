"""Browsing methods for APKMirror."""

from typing import Self

from src.browser.browser import Browser
from src.browser.site import Site, Source


class APKMirror(Site):
    """Sample class to implement methods for APKMirror.

    Implementing these would do the work.
    """

    def __init__(self: Self, browser: Browser) -> None:
        super().__init__(browser)

    async def get(self: Self, url: str, timeout: float) -> Source:  # noqa: D102
        return await super().get(url, timeout)

    async def check_if_loaded(self: Self) -> bool:  # noqa: D102
        return await super().check_if_loaded()
