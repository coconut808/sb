import re
from datetime import datetime
from pathlib import Path

import pytest

from second_brain.notes import list_notes, read_note, slugify, write_note


def test_slugify_basic():
    assert slugify("My brilliant idea about caching") == "my-brilliant-idea-about-caching"


def test_slugify_ascii_folds_unicode():
    assert slugify("café résumé") == "cafe-resume"


def test_slugify_strips_punctuation():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_collapses_whitespace_and_dashes():
    assert slugify("  Multiple   spaces -- here ") == "multiple-spaces-here"


def test_slugify_truncates_long_text():
    long = "word " * 50
    assert len(slugify(long)) <= 60


def test_slugify_empty_input_falls_back():
    assert slugify("") == "note"


def test_slugify_pure_emoji_falls_back():
    assert slugify("🎉🎉🎉") == "note"


def test_write_note_writes_h1_only(tmp_path):
    when = datetime(2026, 5, 7, 9, 30, 45)
    path = write_note("My brilliant idea", str(tmp_path), now=when)
    assert path.read_text() == "# My brilliant idea\n"


def test_write_note_filename_format(tmp_path):
    when = datetime(2026, 5, 7, 9, 30, 45)
    path = write_note("My brilliant idea", str(tmp_path), now=when)
    assert path.name == "2026-05-07-093045-my-brilliant-idea.md"


def test_write_note_creates_directory_if_missing(tmp_path):
    target = tmp_path / "does-not-exist" / "nested"
    when = datetime(2026, 5, 7, 9, 30, 45)
    path = write_note("hello", str(target), now=when)
    assert target.is_dir()
    assert path.parent == target.resolve()


def test_write_note_returns_absolute_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    when = datetime(2026, 5, 7, 9, 30, 45)
    path = write_note("hello", "./relative-notes", now=when)
    assert path.is_absolute()


def test_write_note_expanduser(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    when = datetime(2026, 5, 7, 9, 30, 45)
    path = write_note("hello", "~/sb-notes", now=when)
    assert (tmp_path / "sb-notes").is_dir()
    assert path.parent.resolve() == (tmp_path / "sb-notes").resolve()


def test_write_note_default_now(tmp_path):
    path = write_note("hello", str(tmp_path))
    assert re.match(r"^\d{4}-\d{2}-\d{2}-\d{6}-hello\.md$", path.name)


def test_list_notes_returns_markdown_newest_first(tmp_path):
    (tmp_path / "2026-05-06-094501-old.md").write_text("# old\n")
    (tmp_path / "2026-05-07-093045-new.md").write_text("# new\n")
    result = list_notes(str(tmp_path))
    assert [p.name for p in result] == [
        "2026-05-07-093045-new.md",
        "2026-05-06-094501-old.md",
    ]


def test_list_notes_filters_non_markdown(tmp_path):
    (tmp_path / "2026-05-07-093045-keep.md").write_text("# keep\n")
    (tmp_path / "ignore.txt").write_text("nope")
    (tmp_path / "ignore.markdown").write_text("nope")
    (tmp_path / ".hidden").write_text("nope")
    result = list_notes(str(tmp_path))
    assert [p.name for p in result] == ["2026-05-07-093045-keep.md"]


def test_list_notes_does_not_recurse(tmp_path):
    (tmp_path / "top.md").write_text("# top\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("# nested\n")
    result = list_notes(str(tmp_path))
    assert [p.name for p in result] == ["top.md"]


def test_list_notes_creates_missing_dir(tmp_path):
    target = tmp_path / "does-not-exist" / "nested"
    assert list_notes(str(target)) == []
    assert target.is_dir()


def test_list_notes_empty_dir_returns_empty_list(tmp_path):
    assert list_notes(str(tmp_path)) == []


def test_list_notes_expanduser(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path).mkdir(parents=True, exist_ok=True)
    notes_root = tmp_path / "sb-list-notes"
    notes_root.mkdir()
    (notes_root / "2026-05-07-093045-hi.md").write_text("# hi\n")
    result = list_notes("~/sb-list-notes")
    assert [p.name for p in result] == ["2026-05-07-093045-hi.md"]


def test_read_note_resolves_index_newest_first(tmp_path):
    (tmp_path / "2026-05-06-094501-old.md").write_text("# old\n")
    (tmp_path / "2026-05-07-093045-new.md").write_text("# new\n")
    path, content = read_note(str(tmp_path), "1")
    assert path.name == "2026-05-07-093045-new.md"
    assert content == "# new\n"


def test_read_note_resolves_filename(tmp_path):
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo\nbody\n")
    path, content = read_note(str(tmp_path), "2026-05-07-093045-foo.md")
    assert path.name == "2026-05-07-093045-foo.md"
    assert content == "# foo\nbody\n"


def test_read_note_index_out_of_range(tmp_path):
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo\n")
    with pytest.raises(IndexError, match="only 1 notes"):
        read_note(str(tmp_path), "5")


def test_read_note_index_zero(tmp_path):
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo\n")
    with pytest.raises(IndexError):
        read_note(str(tmp_path), "0")


def test_read_note_index_in_empty_dir(tmp_path):
    with pytest.raises(IndexError, match="no notes"):
        read_note(str(tmp_path), "1")


def test_read_note_filename_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="no such note"):
        read_note(str(tmp_path), "nope.md")


def test_read_note_rejects_path_traversal_dotdot(tmp_path):
    with pytest.raises(ValueError):
        read_note(str(tmp_path), "../etc/passwd")


def test_read_note_rejects_path_separator(tmp_path):
    with pytest.raises(ValueError):
        read_note(str(tmp_path), "subdir/foo.md")


def test_read_note_rejects_backslash(tmp_path):
    with pytest.raises(ValueError):
        read_note(str(tmp_path), "subdir\\foo.md")


def test_read_note_rejects_empty(tmp_path):
    with pytest.raises(ValueError):
        read_note(str(tmp_path), "")


def test_read_note_rejects_whitespace(tmp_path):
    with pytest.raises(ValueError):
        read_note(str(tmp_path), "   ")


def test_read_note_does_not_create_missing_dir(tmp_path):
    target = tmp_path / "does-not-exist"
    with pytest.raises(IndexError):
        read_note(str(target), "1")
    assert not target.exists()


def test_read_note_missing_dir_filename(tmp_path):
    target = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        read_note(str(target), "foo.md")
    assert not target.exists()


def test_read_note_expanduser(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    notes_root = tmp_path / "sb-read-notes"
    notes_root.mkdir()
    (notes_root / "2026-05-07-093045-hi.md").write_text("# hi\n")
    path, content = read_note("~/sb-read-notes", "1")
    assert path.name == "2026-05-07-093045-hi.md"
    assert content == "# hi\n"
