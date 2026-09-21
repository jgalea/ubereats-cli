import json
import urllib.parse

import pytest

from ubereats import location
from ubereats.errors import LocationError
from ubereats.models import Address


class FakeGeoResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeGeoTransport:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        return FakeGeoResponse(self.payload)


NOMINATIM = [
    {
        "lat": "38.6959220",
        "lon": "-9.3774938",
        "display_name": "Avenida Marginal, Areias, Cascais, Portugal",
    },
    {
        "lat": "38.6975412",
        "lon": "-9.3814127",
        "display_name": "Avenida Marginal, Sao Joao do Estoril, Portugal",
    },
]


def test_geocode_maps_results_to_addresses():
    t = FakeGeoTransport(NOMINATIM)
    out = location.geocode("Avenida Marginal, Cascais", transport=t)
    assert len(out) == 2
    assert out[0].latitude == 38.6959220
    assert out[0].longitude == -9.3774938
    assert out[0].label == "Avenida Marginal"
    assert out[0].formatted == "Avenida Marginal, Areias, Cascais, Portugal"


def test_geocode_identifies_itself_to_nominatim():
    t = FakeGeoTransport(NOMINATIM)
    location.geocode("x", transport=t)
    assert t.calls[0]["headers"]["user-agent"] == location.GEOCODER_UA
    assert t.calls[0]["params"]["format"] == "json"


def test_geocode_raises_when_nothing_matches():
    t = FakeGeoTransport([])
    with pytest.raises(LocationError) as e:
        location.geocode("nowhere at all", transport=t)
    assert "nowhere at all" in str(e.value)


def test_loc_cookie_value_is_url_encoded_json_with_coordinates():
    a = Address(label="Home", latitude=38.69, longitude=-9.42, formatted="Cascais, Portugal")
    raw = json.loads(urllib.parse.unquote(location.loc_cookie_value(a)))
    assert raw["latitude"] == 38.69
    assert raw["longitude"] == -9.42
    assert raw["address"]["title"] == "Home"
    assert raw["address"]["eaterFormattedAddress"] == "Cascais, Portugal"
    assert raw["referenceType"] == "google_places"


def test_save_and_load_address_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    a = Address(label="Home", latitude=38.69, longitude=-9.42, formatted="Cascais")
    location.save_address(a)
    assert location.load_address() == a


def test_load_address_raises_when_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    with pytest.raises(LocationError) as e:
        location.load_address()
    assert "ubereats address" in str(e.value)


def test_apply_to_sets_the_cookie_pair():
    class FakeSession:
        def __init__(self):
            self.cookies = {}

        def set_cookie(self, name, value):
            self.cookies[name] = value

    s = FakeSession()
    location.apply_to(s, Address(label="H", latitude=1.0, longitude=2.0, formatted="F"))
    assert "uev2.loc" in s.cookies
    assert s.cookies["uev2.diningMode"] == "DELIVERY"
