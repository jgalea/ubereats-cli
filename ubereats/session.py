import os
import sys

from . import config
from .errors import ApiError, ChallengeError, NotFoundError

CHALLENGE_MARKERS = (
    "Just a moment",
    "cf-browser-verification",
    "Attention Required! | Cloudflare",
    "Verifying you are human",
)


def _default_transport(impersonate: str):
    from curl_cffi import requests

    return requests.Session(impersonate=impersonate)


class Session:
    API_BASE = "https://www.ubereats.com/_p/api"

    def __init__(self, locale: str = "pt", impersonate: str = "chrome", transport=None):
        self.locale = locale
        self.impersonate = impersonate
        self._transport = transport if transport is not None else _default_transport(impersonate)
        self._debug = bool(os.environ.get("UBEREATS_DEBUG"))

    def _headers(self) -> dict:
        return {
            "content-type": "application/json",
            "x-csrf-token": "x",
            "accept": "*/*",
            "accept-language": f"{self.locale},en;q=0.9",
            "origin": "https://www.ubereats.com",
            "referer": "https://www.ubereats.com/",
        }

    def _is_challenge(self, response) -> bool:
        if any(marker in response.text for marker in CHALLENGE_MARKERS):
            return True
        if response.status_code not in (403, 503):
            return False
        return self._botdefense_state(response) is None

    def _botdefense_state(self, response) -> str | None:
        try:
            body = response.json()
        except Exception:
            return None
        if not isinstance(body, dict):
            return None
        return ((body.get("metadata") or {}).get("botdefense") or {}).get("state")

    def api(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.API_BASE}/{endpoint}?localeCode={self.locale}"
        response = self._post(url, payload)
        state = self._botdefense_state(response)
        if state and state != "allow":
            raise ChallengeError(
                f"Uber's bot defense is challenging this machine (state: {state}). "
                "This is Uber's own check, not Cloudflare, and retrying will not clear "
                "it. It usually follows a burst of requests from one address. Open "
                "ubereats.com in a browser on this connection, complete the check, then "
                "wait a few minutes before trying again."
            )
        if self._is_challenge(response):
            self._reset_transport()
            response = self._post(url, payload)
            if self._is_challenge(response):
                raise ChallengeError(
                    "Cloudflare blocked this request twice. Uber is challenging this "
                    "machine; wait a minute and retry, or set UBEREATS_DEBUG=1 to see "
                    "the response."
                )
        return self._unwrap(endpoint, response)

    def _post(self, url: str, payload: dict):
        response = self._transport.post(url, headers=self._headers(), json=payload, timeout=30)
        if self._debug:
            print(f"POST {url} -> {response.status_code}", file=sys.stderr)
            print(f"  request: {payload}", file=sys.stderr)
            print(f"  response: {response.text[:2000]}", file=sys.stderr)
        return response

    def _reset_transport(self) -> None:
        cookies = dict(getattr(self._transport, "cookies", {}) or {})
        self._transport = _default_transport(self.impersonate)
        for name, value in cookies.items():
            self.set_cookie(name, value)

    def _unwrap(self, endpoint: str, response) -> dict:
        try:
            body = response.json()
        except Exception:
            raise ApiError(f"{endpoint} returned a non-JSON response ({response.status_code}).")
        data = body.get("data") or {}
        if body.get("status") == "success":
            return data
        code = data.get("code", "")
        message = data.get("message") or f"{endpoint} failed ({response.status_code})."
        if code == "ERR_MISSING_HANDLER" or response.status_code == 404:
            raise NotFoundError(f"{endpoint}: {message}")
        raise ApiError(f"{endpoint}: {message}")

    def set_cookie(self, name: str, value: str) -> None:
        cookies = self._transport.cookies
        if hasattr(cookies, "set"):
            cookies.set(name, value, domain=".ubereats.com")
        else:
            cookies[name] = value

    def save(self) -> None:
        cookies = self._transport.cookies
        items = dict(cookies.items()) if hasattr(cookies, "items") else dict(cookies)
        config.write_json(config.cookies_path(), items, mode=0o600)

    def load(self) -> None:
        for name, value in (config.read_json(config.cookies_path()) or {}).items():
            self.set_cookie(name, value)
