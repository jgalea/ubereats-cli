import pytest

from ubereats.models import Address, Item, Menu, MenuSection, Store, format_price


def test_models_are_immutable():
    s = Store(uuid="u", title="T")
    with pytest.raises(Exception):
        s.title = "other"


def test_menu_counts_items_across_sections():
    a = Item(uuid="1", title="A", price=100)
    b = Item(uuid="2", title="B", price=200)
    m = Menu(
        store_uuid="s",
        title="Store",
        currency="EUR",
        eta="20 min",
        sections=(MenuSection(title="One", items=(a,)), MenuSection(title="Two", items=(b,))),
    )
    assert m.item_count == 2


def test_format_price_converts_minor_units():
    assert format_price(2199, "EUR") == "21.99 EUR"
    assert format_price(0, "EUR") == "0.00 EUR"
    assert format_price(5, "USD") == "0.05 USD"


def test_address_holds_coordinates():
    a = Address(label="Home", latitude=38.69, longitude=-9.42, formatted="Cascais")
    assert (a.latitude, a.longitude) == (38.69, -9.42)
