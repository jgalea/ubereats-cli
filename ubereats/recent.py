from . import config

_FILE = "recent.json"


def _path():
    return config.config_dir() / _FILE


def save(kind: str, uuids: list[str]) -> None:
    data = config.read_json(_path()) or {}
    data[kind] = uuids
    config.write_json(_path(), data, mode=0o600)


def lookup(kind: str, index: int) -> str | None:
    data = config.read_json(_path()) or {}
    uuids = data.get(kind) or []
    if 1 <= index <= len(uuids):
        return uuids[index - 1]
    return None
