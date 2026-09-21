import stat

from ubereats import config
from ubereats.errors import UberEatsError, ChallengeError, AuthError, ApiError


def test_config_dir_honours_env(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path / "cfg"))
    d = config.config_dir()
    assert d == tmp_path / "cfg"
    assert d.is_dir()
    assert stat.S_IMODE(d.stat().st_mode) == 0o700


def test_config_dir_defaults_to_home(tmp_path, monkeypatch):
    monkeypatch.delenv("UBEREATS_CONFIG_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert config.config_dir() == tmp_path / ".ubereats"


def test_paths_sit_inside_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    assert config.cookies_path() == tmp_path / "cookies.json"
    assert config.location_path() == tmp_path / "location.json"
    assert config.auth_path() == tmp_path / "auth.json"
    assert config.exclude_path() == tmp_path / "exclude.txt"


def test_write_json_is_owner_only_and_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    p = config.auth_path()
    config.write_json(p, {"sid": "secret"})
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert config.read_json(p) == {"sid": "secret"}


def test_read_json_returns_none_when_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    assert config.read_json(tmp_path / "nope.json") is None


def test_read_json_returns_none_on_corrupt_file(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert config.read_json(p) is None


def test_error_exit_codes():
    assert UberEatsError.exit_code == 1
    assert ChallengeError.exit_code == 4
    assert AuthError.exit_code == 5
    assert ApiError.exit_code == 8
    assert isinstance(ChallengeError("x"), UberEatsError)
