import base64
import re
import uuid as uuidlib

from .errors import NotFoundError
from .models import Item, Menu, MenuSection

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def resolve_store(ref: str) -> str:
    ref = ref.strip()
    if UUID_RE.match(ref):
        return ref.lower()
    segment = ref.rstrip("/").split("/")[-1].split("?")[0]
    try:
        raw = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        return str(uuidlib.UUID(bytes=raw))
    except Exception:
        raise NotFoundError(
            f"{ref!r} is not a store. Pass a store uuid or a ubereats.com/store/... URL."
        )


def _text(value):
    if isinstance(value, dict):
        return value.get("text")
    return value


def _to_item(raw: dict) -> Item | None:
    if not raw.get("uuid") or not raw.get("title"):
        return None
    return Item(
        uuid=raw["uuid"],
        title=raw["title"],
        price=int(raw.get("price") or 0),
        description=raw.get("itemDescription") or None,
        sold_out=bool(raw.get("isSoldOut")),
        customizable=bool(raw.get("hasCustomizations")),
        section_uuid=raw.get("sectionUuid"),
    )


def parse_menu(data: dict, store_uuid: str) -> Menu:
    data = data or {}
    sections = []
    for entries in (data.get("catalogSectionsMap") or {}).values():
        for entry in entries or []:
            payload = (entry.get("payload") or {}).get("standardItemsPayload") or {}
            raw_items = payload.get("catalogItems") or []
            items = tuple(i for i in (_to_item(r) for r in raw_items) if i is not None)
            if not items:
                continue
            sections.append(MenuSection(title=_text(payload.get("title")) or "", items=items))
    return Menu(
        store_uuid=store_uuid,
        title=data.get("title") or "",
        currency=data.get("currencyCode") or "EUR",
        eta=_text(data.get("etaRange")),
        sections=tuple(sections),
    )


def menu(session, ref: str) -> Menu:
    store_uuid = resolve_store(ref)
    data = session.api("getStoreV1", {"storeUuid": store_uuid})
    return parse_menu(data, store_uuid)
