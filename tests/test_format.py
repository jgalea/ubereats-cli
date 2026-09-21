import json

from ubereats.format import to_jsonable, to_toon
from ubereats.models import Item, Menu, MenuSection, Store


def test_to_jsonable_converts_dataclasses():
    out = to_jsonable([Store(uuid="1", title="A", eta="20 min")])
    assert out == [
        {"uuid": "1", "title": "A", "url": None, "rating": None, "eta": "20 min", "image": None}
    ]
    json.dumps(out)


def test_to_jsonable_converts_nested_menus():
    m = Menu(
        store_uuid="s",
        title="T",
        currency="EUR",
        eta=None,
        sections=(MenuSection(title="One", items=(Item(uuid="i", title="X", price=100),)),),
    )
    out = to_jsonable(m)
    assert out["sections"][0]["items"][0]["price"] == 100


def test_to_toon_emits_a_header_and_rows():
    rows = [
        {"uuid": "1", "title": "Sushi", "eta": "20 min"},
        {"uuid": "2", "title": "Pizza", "eta": "30 min"},
    ]
    lines = to_toon(rows, root="stores").splitlines()
    assert lines[0] == "stores[2]{uuid,title,eta}:"
    assert lines[1] == "  1,Sushi,20 min"
    assert lines[2] == "  2,Pizza,30 min"


def test_to_toon_quotes_values_containing_commas():
    assert to_toon([{"title": "Rice, beans"}], root="x").splitlines()[1] == '  "Rice, beans"'


def test_to_toon_doubles_internal_quotes():
    out = to_toon([{"title": 'He said "hi"'}], root="x")
    assert out.splitlines()[1] == '  "He said ""hi"""'


def test_to_toon_renders_none_as_empty():
    assert to_toon([{"a": None, "b": 1}], root="x").splitlines()[1] == "  ,1"


def test_to_toon_empty_list():
    assert to_toon([], root="stores") == "stores[0]{}:"


def test_to_toon_falls_back_for_a_mapping():
    out = to_toon({"title": "T", "currency": "EUR"}, root="menu")
    assert "title: T" in out
    assert "currency: EUR" in out
