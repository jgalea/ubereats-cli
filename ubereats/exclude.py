from . import config


def load_exclusions(spec: str | None) -> list[str]:
    if spec is not None:
        if spec.strip().lower() == "none":
            return []
        return [part.strip().lower() for part in spec.split(",") if part.strip()]
    path = config.exclude_path()
    if not path.exists():
        return []
    names = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.append(line.lower())
    return names


def apply(stores, names):
    if not names:
        return list(stores), []
    kept, hidden = [], []
    for store in stores:
        title = store.title.lower()
        (hidden if any(name in title for name in names) else kept).append(store)
    return kept, hidden
