from ubereats import exclude
from ubereats.models import Store

STORES = [
    Store(uuid="1", title="Domino's Pizza"),
    Store(uuid="2", title="Sushi Yatomi"),
    Store(uuid="3", title="PIZZA HUT Cascais"),
]


def test_apply_hides_by_case_insensitive_substring():
    kept, hidden = exclude.apply(STORES, ["domino", "pizza hut"])
    assert [s.title for s in kept] == ["Sushi Yatomi"]
    assert len(hidden) == 2


def test_apply_with_no_names_keeps_everything():
    kept, hidden = exclude.apply(STORES, [])
    assert len(kept) == 3
    assert hidden == []


def test_load_exclusions_parses_a_comma_list(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    assert exclude.load_exclusions("domino, pizza hut ") == ["domino", "pizza hut"]


def test_load_exclusions_none_disables_the_filter(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    (tmp_path / "exclude.txt").write_text("domino\n")
    assert exclude.load_exclusions("none") == []


def test_load_exclusions_reads_the_file_when_flag_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    (tmp_path / "exclude.txt").write_text("domino\n\n# a comment\npizza hut\n")
    assert exclude.load_exclusions(None) == ["domino", "pizza hut"]


def test_load_exclusions_with_no_file_is_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("UBEREATS_CONFIG_DIR", str(tmp_path))
    assert exclude.load_exclusions(None) == []
