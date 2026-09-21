import json
from pathlib import Path

from ubereats.search import parse_search, search

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "search_feed.json").read_text())


def test_parse_search_skips_non_store_feed_items():
    assert len(parse_search(FIXTURE["data"])) == 2


def test_parse_search_reads_store_fields():
    first = parse_search(FIXTURE["data"])[0]
    assert first.uuid
    assert first.title
    assert first.url.startswith("/store/")


def test_parse_search_tolerates_missing_rating_and_eta():
    second = parse_search(FIXTURE["data"])[1]
    assert second.rating is None
    assert second.eta is None
    assert second.title


def test_parse_search_handles_empty_feed():
    assert parse_search({"feedItems": []}) == []
    assert parse_search({}) == []


def test_search_sends_the_documented_payload():
    captured = {}

    class FakeSession:
        def api(self, endpoint, payload):
            captured["endpoint"] = endpoint
            captured["payload"] = payload
            return FIXTURE["data"]

    out = search(FakeSession(), "sushi", limit=7)
    assert captured["endpoint"] == "getSearchFeedV1"
    assert captured["payload"]["userQuery"] == "sushi"
    assert captured["payload"]["pageInfo"] == {"offset": 0, "pageSize": 7}
    assert captured["payload"]["source"] == "SEARCH_SUGGESTION"
    assert captured["payload"]["vertical"] == "ALL"
    assert len(out) == 2
