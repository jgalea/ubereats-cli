import json
import os
from pathlib import Path


def config_dir() -> Path:
    override = os.environ.get("UBEREATS_CONFIG_DIR")
    path = Path(override) if override else Path.home() / ".ubereats"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def cookies_path() -> Path:
    return config_dir() / "cookies.json"


def location_path() -> Path:
    return config_dir() / "location.json"


def auth_path() -> Path:
    return config_dir() / "auth.json"


def exclude_path() -> Path:
    return config_dir() / "exclude.txt"


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, data, *, mode: int = 0o600) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False))
    os.chmod(tmp, mode)
    os.replace(tmp, path)
