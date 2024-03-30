"""Methods for managing browser tab cookies."""

import json
from collections.abc import Iterator
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Self

from requests.cookies import create_cookie


class Cookies:
    """Represent the stored cookies from the browser."""

    def __init__(self: Self) -> None:
        self.cookies_file: Path = Path.cwd().joinpath("browser_cookies.json")
        self.cookies: list[dict[str, Any]] = []
        self._load_cookies_from_file()

    def update_cookie(self: Self, cookie_dict: dict[str, Any]) -> None:
        """Update the cookie list by adding another cookie."""
        self.cookies = list(filter(lambda _cookie: not self._are_cookies_matching(cookie_dict, _cookie), self.cookies))
        self.cookies.append(cookie_dict)
        self.save_cookies()

    def update_cookies(self: Self, cookie_list: list[dict[str, Any]]) -> None:
        """Update the cookie list by extending another cookie list."""
        for cookie in cookie_list:
            self.update_cookie(cookie)

    def load_to_cookie_jar(self: Self) -> CookieJar:
        """Loads the stored cookies into the cookie jar."""
        cookie_jar = CookieJar()
        for _cookie in self.cookies:
            cookie = create_cookie(
                name=_cookie["name"],
                value=_cookie["value"],
                domain=_cookie["domain"],
                path=_cookie["path"],
                expires=_cookie["expires"],
                secure=_cookie["secure"],
                rest={"HttpOnly": _cookie["httpOnly"]},
            )
            cookie_jar.set_cookie(cookie)
        return cookie_jar

    def save_cookies(self: Self) -> None:
        """Save the cookies to the file."""
        self._save_cookies_to_file()

    def delete_cookies(self: Self) -> None:
        """Delete the saved cookies file."""
        self.cookies_file.unlink(missing_ok=True)

    @staticmethod
    def _are_cookies_matching(cookie_new: dict[str, Any], cookie_old: dict[str, Any]) -> bool:
        return (
            cookie_new["name"] == cookie_old["name"]
            and cookie_new["domain"] == cookie_old["domain"]
            and cookie_new["path"] == cookie_old["path"]
        )

    def _load_cookies_from_file(self: Self) -> list[dict[str, Any]]:
        if self.cookies_file.exists():
            try:
                self.cookies = json.loads(self.cookies_file.read_text())
            except ValueError:
                self.cookies = []
        return self.cookies

    def _save_cookies_to_file(self: Self) -> bool:
        try:
            with self.cookies_file.open("w") as f:
                json.dump(self.cookies, f)
        except Exception:  # noqa: BLE001
            return False
        else:
            return True

    def __iter__(self: Self) -> Iterator[dict[str, Any]]:
        """Returns an iterator cookies."""
        return self.cookies.__iter__()
