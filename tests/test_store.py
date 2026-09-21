import json
from pathlib import Path

import pytest

from ubereats.errors import NotFoundError
from ubereats.store import menu, parse_menu, resolve_store

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "store_menu.json").read_text())


def test_resolve_store_passes_through_a_uuid():
    u = "7d407eb1-10bd-4889-aaf5-f92237a6b587"
    assert resolve_store(u) == u


def test_resolve_store_decodes_a_url_segment():
    url = "https://www.ubereats.com/pt/store/el-corte-ingles/fUB-sRC9SImq9fkiN6a1hw"
    assert resolve_store(url) == "7d407eb1-10bd-4889-aaf5-f92237a6b587"


def test_resolve_store_decodes_a_bare_path():
    assert resolve_store("/store/x/fUB-sRC9SImq9fkiN6a1hw") == "7d407eb1-10bd-4889-aaf5-f92237a6b587"


def test_resolve_store_rejects_nonsense():
    with pytest.raises(NotFoundError):
        resolve_store("not a store at all")


def test_parse_menu_reads_store_header():
    m = parse_menu(FIXTURE["data"], "abc")
    assert m.store_uuid == "abc"
    assert m.title
    assert m.currency == "EUR"
    assert m.eta


def test_parse_menu_skips_aisle_sections():
    assert len(parse_menu(FIXTURE["data"], "abc").sections) == 2


def test_parse_menu_reads_items_with_integer_prices():
    m = parse_menu(FIXTURE["data"], "abc")
    item = m.sections[0].items[0]
    assert isinstance(item.price, int)
    assert item.uuid
    assert item.title
    assert m.item_count == 6


def test_parse_menu_on_an_empty_store():
    m = parse_menu({"title": "X", "currencyCode": "EUR"}, "abc")
    assert m.sections == ()
    assert m.item_count == 0


def test_menu_sends_the_store_uuid():
    captured = {}

    class FakeSession:
        def api(self, endpoint, payload):
            captured["endpoint"] = endpoint
            captured["payload"] = payload
            return FIXTURE["data"]

    out = menu(FakeSession(), "7d407eb1-10bd-4889-aaf5-f92237a6b587")
    assert captured["endpoint"] == "getStoreV1"
    assert captured["payload"] == {"storeUuid": "7d407eb1-10bd-4889-aaf5-f92237a6b587"}
    assert out.item_count == 6
