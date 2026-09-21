import json

import pytest

from ubereats.errors import ApiError, ChallengeError, NotFoundError
from ubereats.session import CHALLENGE_MARKERS, Session


class FakeResponse:
    def __init__(self, status_code, body, *, is_json=True):
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body) if is_json else body
        self._is_json = is_json
        self.headers = {"content-type": "application/json" if is_json else "text/html"}

    def json(self):
        if not self._is_json:
            raise ValueError("not json")
        return self._body


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.cookies = {}

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.responses.pop(0)


def test_api_returns_data_and_sends_required_headers():
    t = FakeTransport([FakeResponse(200, {"status": "success", "data": {"ok": 1}})])
    s = Session(transport=t)
    assert s.api("getSearchFeedV1", {"userQuery": "sushi"}) == {"ok": 1}
    call = t.calls[0]
    assert call["url"] == "https://www.ubereats.com/_p/api/getSearchFeedV1?localeCode=pt"
    assert call["headers"]["x-csrf-token"] == "x"
    assert call["headers"]["content-type"] == "application/json"
    assert call["headers"]["origin"] == "https://www.ubereats.com"
    assert call["headers"]["referer"] == "https://www.ubereats.com/"
    assert call["json"] == {"userQuery": "sushi"}


def test_locale_is_used_in_the_query_string():
    t = FakeTransport([FakeResponse(200, {"status": "success", "data": {}})])
    Session(locale="es", transport=t).api("getStoreV1", {})
    assert t.calls[0]["url"].endswith("?localeCode=es")


def test_cloudflare_challenge_is_retried_once_then_raises(monkeypatch):
    challenge = FakeResponse(403, "<html><title>Just a moment...</title></html>", is_json=False)
    t = FakeTransport([challenge, challenge])
    monkeypatch.setattr("ubereats.session._default_transport", lambda impersonate: t)
    with pytest.raises(ChallengeError) as e:
        Session(transport=t).api("getStoreV1", {})
    assert len(t.calls) == 2
    assert "cloudflare" in str(e.value).lower()


def test_challenge_then_success_recovers(monkeypatch):
    t = FakeTransport([
        FakeResponse(403, "<html><title>Just a moment...</title></html>", is_json=False),
        FakeResponse(200, {"status": "success", "data": {"ok": 2}}),
    ])
    monkeypatch.setattr("ubereats.session._default_transport", lambda impersonate: t)
    assert Session(transport=t).api("getStoreV1", {}) == {"ok": 2}


def test_missing_handler_raises_not_found():
    body = {
        "status": "failure",
        "data": {"message": "Missing RPC handler for x", "code": "ERR_MISSING_HANDLER"},
    }
    t = FakeTransport([FakeResponse(404, body), FakeResponse(404, body)])
    with pytest.raises(NotFoundError):
        Session(transport=t).api("nope", {})


def test_failure_status_raises_api_error_with_server_message():
    body = {"status": "failure", "data": {"message": "store closed", "code": "ERR_X"}}
    t = FakeTransport([FakeResponse(200, body)])
    with pytest.raises(ApiError) as e:
        Session(transport=t).api("getStoreV1", {})
    assert "store closed" in str(e.value)


def test_cookies_round_trip_through_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    s = Session(transport=FakeTransport([]))
    s.set_cookie("uev2.loc", "encoded")
    s.save()
    t2 = FakeTransport([])
    Session(transport=t2).load()
    assert t2.cookies["uev2.loc"] == "encoded"


def test_challenge_markers_cover_the_interstitial():
    assert any(m in "<title>Just a moment...</title>" for m in CHALLENGE_MARKERS)


@pytest.mark.network
def test_live_api_clears_cloudflare():
    s = Session()
    data = s.api(
        "getSearchFeedV1",
        {
            "userQuery": "pizza",
            "keyName": "",
            "pageInfo": {"offset": 0, "pageSize": 5},
            "sortAndFilters": [],
            "source": "SEARCH_SUGGESTION",
            "vertical": "ALL",
        },
    )
    assert "feedItems" in data
