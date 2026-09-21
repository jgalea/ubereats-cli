import json

import pytest
from typer.testing import CliRunner

from ubereats.cli import app
from ubereats.models import Item, Menu, MenuSection, Store

runner = CliRunner()

FIXTURE_STORES = [
    Store(uuid="u1", title="Sushi Yatomi", eta="59 min", rating="4.6", url="/store/x/y")
]
FIXTURE_MENU = Menu(
    store_uuid="u1",
    title="Sushi Yatomi",
    currency="EUR",
    eta="59 min",
    sections=(MenuSection(title="Ofertas", items=(Item(uuid="i1", title="Simple Box 4", price=2199),)),),
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))


def _saved_address():
    from ubereats import location
    from ubereats.models import Address

    location.save_address(Address(label="H", latitude=1.0, longitude=2.0, formatted="H"))


def test_version_prints_the_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip()


def test_search_requires_an_address():
    result = runner.invoke(app, ["search", "sushi"])
    assert result.exit_code == 6
    assert "ubereats address" in result.stdout


def test_address_saves_the_first_match(monkeypatch):
    from ubereats import location
    from ubereats.models import Address

    monkeypatch.setattr(
        location,
        "geocode",
        lambda q, **kw: [
            Address(
                label="Avenida Marginal",
                latitude=38.69,
                longitude=-9.37,
                formatted="Avenida Marginal, Cascais",
            )
        ],
    )
    result = runner.invoke(app, ["address", "Avenida Marginal, Cascais"])
    assert result.exit_code == 0
    assert "Avenida Marginal" in result.stdout
    assert location.load_address().latitude == 38.69


def test_address_with_no_argument_shows_the_saved_one():
    from ubereats import location
    from ubereats.models import Address

    location.save_address(Address(label="Home", latitude=1.0, longitude=2.0, formatted="Home, Cascais"))
    result = runner.invoke(app, ["address"])
    assert result.exit_code == 0
    assert "Home, Cascais" in result.stdout


def test_search_json_output(monkeypatch):
    from ubereats import cli

    _saved_address()
    monkeypatch.setattr(cli, "build_session", lambda *a, **kw: object())
    monkeypatch.setattr(cli, "do_search", lambda session, query, limit: FIXTURE_STORES)
    result = runner.invoke(app, ["search", "sushi", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["title"] == "Sushi Yatomi"


def test_search_reports_hidden_stores(monkeypatch):
    from ubereats import cli

    _saved_address()
    monkeypatch.setattr(cli, "build_session", lambda *a, **kw: object())
    monkeypatch.setattr(cli, "do_search", lambda session, query, limit: FIXTURE_STORES)
    result = runner.invoke(app, ["search", "sushi", "--exclude", "sushi"])
    assert result.exit_code == 0
    assert "hidden" in result.output.lower()


def test_menu_toon_output(monkeypatch):
    from ubereats import cli

    _saved_address()
    monkeypatch.setattr(cli, "build_session", lambda *a, **kw: object())
    monkeypatch.setattr(cli, "do_menu", lambda session, ref: FIXTURE_MENU)
    result = runner.invoke(app, ["menu", "u1", "--toon"])
    assert result.exit_code == 0
    assert result.stdout.splitlines()[0].startswith("items[1]{")


def test_api_errors_exit_with_their_code(monkeypatch):
    from ubereats import cli
    from ubereats.errors import ChallengeError

    _saved_address()
    monkeypatch.setattr(cli, "build_session", lambda *a, **kw: object())

    def boom(session, query, limit):
        raise ChallengeError("Cloudflare blocked this request twice.")

    monkeypatch.setattr(cli, "do_search", boom)
    result = runner.invoke(app, ["search", "sushi"])
    assert result.exit_code == 4
    assert "Cloudflare" in result.stdout
