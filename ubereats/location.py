import json
import urllib.parse

from . import config
from .errors import LocationError
from .models import Address

GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_UA = "ubereats-cli (https://github.com/jgalea/ubereats-cli)"


def _default_transport():
    from curl_cffi import requests

    return requests.Session(impersonate="chrome")


def geocode(query: str, *, limit: int = 5, transport=None) -> list[Address]:
    client = transport if transport is not None else _default_transport()
    response = client.get(
        GEOCODER_URL,
        params={"q": query, "format": "json", "limit": str(limit), "addressdetails": "1"},
        headers={"user-agent": GEOCODER_UA},
        timeout=30,
    )
    results = response.json()
    if not results:
        raise LocationError(
            f"No address matched {query!r}. Try a fuller address, or pass --lat and --lng."
        )
    return [
        Address(
            label=item["display_name"].split(",")[0].strip(),
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            formatted=item["display_name"],
        )
        for item in results
    ]


def loc_cookie_value(address: Address) -> str:
    payload = {
        "address": {
            "address1": address.label,
            "address2": "",
            "aptOrSuite": "",
            "eaterFormattedAddress": address.formatted,
            "subtitle": address.formatted,
            "title": address.label,
            "uuid": "",
        },
        "latitude": address.latitude,
        "longitude": address.longitude,
        "reference": "",
        "referenceType": "google_places",
        "type": "google_places",
        "source": "manual_auto_complete",
    }
    return urllib.parse.quote(json.dumps(payload))


def save_address(address: Address) -> None:
    config.write_json(
        config.location_path(),
        {
            "label": address.label,
            "latitude": address.latitude,
            "longitude": address.longitude,
            "formatted": address.formatted,
        },
        mode=0o600,
    )


def load_address() -> Address:
    raw = config.read_json(config.location_path())
    if not raw:
        raise LocationError('No delivery address set. Run: ubereats address "<your address>"')
    return Address(
        label=raw["label"],
        latitude=raw["latitude"],
        longitude=raw["longitude"],
        formatted=raw["formatted"],
    )


def apply_to(session, address: Address) -> None:
    session.set_cookie("uev2.loc", loc_cookie_value(address))
    session.set_cookie("uev2.diningMode", "DELIVERY")
