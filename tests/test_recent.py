from ubereats import recent


def test_save_and_lookup_is_one_based(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    recent.save("stores", ["aaa", "bbb", "ccc"])
    assert recent.lookup("stores", 1) == "aaa"
    assert recent.lookup("stores", 3) == "ccc"


def test_lookup_out_of_range_is_none(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    recent.save("stores", ["aaa"])
    assert recent.lookup("stores", 0) is None
    assert recent.lookup("stores", 2) is None


def test_lookup_with_nothing_saved(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    assert recent.lookup("stores", 1) is None


def test_kinds_do_not_collide(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    recent.save("stores", ["s1"])
    recent.save("items", ["i1"])
    assert recent.lookup("stores", 1) == "s1"
    assert recent.lookup("items", 1) == "i1"
