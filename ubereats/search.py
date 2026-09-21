from .models import Store


def _text(value):
    if isinstance(value, dict):
        return value.get("text")
    return value


def _eta(store: dict):
    for badge in store.get("meta") or []:
        if badge.get("badgeType") == "ETD":
            return badge.get("text")
    return None


def _image(store: dict):
    items = (store.get("image") or {}).get("items") or []
    return items[0].get("url") if items else None


def _to_store(entry: dict) -> Store | None:
    store = entry.get("store") or {}
    uuid = store.get("storeUuid") or entry.get("uuid")
    title = _text(store.get("title"))
    if not uuid or not title:
        return None
    return Store(
        uuid=uuid,
        title=title,
        url=store.get("actionUrl"),
        rating=_text(store.get("rating")),
        eta=_eta(store),
        image=_image(store),
    )


def parse_search(data: dict) -> list[Store]:
    stores = []
    for entry in (data or {}).get("feedItems") or []:
        if entry.get("type") != "REGULAR_STORE":
            continue
        store = _to_store(entry)
        if store is not None:
            stores.append(store)
    return stores


def search(session, query: str, *, limit: int = 20) -> list[Store]:
    data = session.api(
        "getSearchFeedV1",
        {
            "userQuery": query,
            "keyName": "",
            "pageInfo": {"offset": 0, "pageSize": limit},
            "sortAndFilters": [],
            "source": "SEARCH_SUGGESTION",
            "vertical": "ALL",
        },
    )
    return parse_search(data)
