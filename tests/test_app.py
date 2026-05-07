import os
import re

from click.testing import CliRunner
from loguru import logger

from second_brain.app import cli, configure_logging


LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| "
    r"(DBG|INF|WRN|ERR|CRT) \| "
    r"[\w.]+:\w+:\d+ \| "
    r".*$",
    re.MULTILINE,
)


def _emit_greeting():
    configure_logging()
    logger.info("Hello from second_brain!")
    logger.remove()


def test_hello_logs_greeting():
    result = CliRunner().invoke(cli, ["hello"])
    assert result.exit_code == 0, result.output
    assert "Hello from second_brain!" in result.output


def test_bare_invocation_lists_subcommands():
    result = CliRunner().invoke(cli, [])
    # Click groups print help and exit non-zero when given no subcommand,
    # but the help should advertise the available subcommands.
    assert "hello" in result.output
    assert "new" in result.output
    assert "list" in result.output


def test_log_format_uses_pipe_separator_and_3letter_level(capfd):
    _emit_greeting()
    captured = capfd.readouterr()
    matching = [line for line in captured.err.splitlines() if LINE_RE.match(line)]
    assert any("INF" in line and "Hello from second_brain!" in line for line in matching)
    assert not re.search(r":\d{2}\.\d", captured.err)
    assert " - Hello from second_brain!" not in captured.err


def test_log_format_applied_to_file_handler():
    _emit_greeting()
    log_file = os.environ["LOG_FILE"]
    with open(log_file) as fh:
        content = fh.read()
    assert any(LINE_RE.match(line) for line in content.splitlines())
    assert "Hello from second_brain!" in content
    assert " - Hello from second_brain!" not in content
    assert not re.search(r":\d{2}\.\d", content)


def test_log_format_abbreviates_each_level(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    configure_logging()
    logger.debug("dmsg")
    logger.info("imsg")
    logger.warning("wmsg")
    logger.error("emsg")
    logger.critical("cmsg")
    logger.remove()

    log_file = os.environ["LOG_FILE"]
    with open(log_file) as fh:
        content = fh.read()

    for abbr, msg in [
        ("DBG", "dmsg"),
        ("INF", "imsg"),
        ("WRN", "wmsg"),
        ("ERR", "emsg"),
        ("CRT", "cmsg"),
    ]:
        assert re.search(rf"\| {abbr} \|.*{msg}", content), (
            f"Expected '{abbr}' line for {msg!r} in:\n{content}"
        )


def test_new_writes_file_and_prints_path(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    result = CliRunner().invoke(cli, ["new", "My brilliant idea"])
    assert result.exit_code == 0, result.output
    written = list(tmp_path.glob("*.md"))
    assert len(written) == 1
    assert written[0].read_text() == "# My brilliant idea\n"
    assert str(written[0]) in result.stdout


def test_new_uses_notes_dir_option_over_env(tmp_path, monkeypatch):
    other = tmp_path / "from-option"
    monkeypatch.setenv("NOTES_DIR", str(tmp_path / "from-env"))
    result = CliRunner().invoke(cli, ["new", "--notes-dir", str(other), "hello"])
    assert result.exit_code == 0, result.output
    assert list(other.glob("*.md"))
    assert not (tmp_path / "from-env").exists()


def test_new_filename_uses_slugified_text(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    result = CliRunner().invoke(cli, ["new", "Café résumé!"])
    assert result.exit_code == 0, result.output
    written = list(tmp_path.glob("*.md"))
    assert len(written) == 1
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}-\d{6}-cafe-resume\.md$",
        written[0].name,
    )


def test_list_renders_path_header_and_numbered_notes(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-06-094501-old.md").write_text("# old\n")
    (tmp_path / "2026-05-07-093045-new.md").write_text("# new\n")
    result = CliRunner().invoke(cli, ["list"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == f"Notes in {tmp_path}:"
    assert lines[1] == ""
    assert lines[2] == "  1. 2026-05-07-093045-new.md"
    assert lines[3] == "  2. 2026-05-06-094501-old.md"


def test_list_empty_directory_shows_empty_message(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    result = CliRunner().invoke(cli, ["list"])
    assert result.exit_code == 0, result.output
    assert f"Notes in {tmp_path}:" in result.output
    assert "(no notes yet)" in result.output


def test_list_missing_directory_is_created_and_empty(tmp_path, monkeypatch):
    target = tmp_path / "does-not-exist"
    monkeypatch.setenv("NOTES_DIR", str(target))
    result = CliRunner().invoke(cli, ["list"])
    assert result.exit_code == 0, result.output
    assert target.is_dir()
    assert "(no notes yet)" in result.output


def test_list_ignores_non_markdown_and_subdirs(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-07-093045-keep.md").write_text("# keep\n")
    (tmp_path / "skip.txt").write_text("nope")
    sub = tmp_path / "nested"
    sub.mkdir()
    (sub / "deep.md").write_text("# deep\n")
    result = CliRunner().invoke(cli, ["list"])
    assert result.exit_code == 0, result.output
    assert "keep.md" in result.output
    assert "skip.txt" not in result.output
    assert "deep.md" not in result.output


def test_list_right_aligns_numbers_for_two_digit_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    for i in range(10):
        (tmp_path / f"2026-05-{i:02d}-093045-note.md").write_text("# n\n")
    result = CliRunner().invoke(cli, ["list"])
    assert result.exit_code == 0, result.output
    assert "   1. " in result.output
    assert "  10. " in result.output


def test_list_uses_notes_dir_option_over_env(tmp_path, monkeypatch):
    other = tmp_path / "from-option"
    other.mkdir()
    (other / "2026-05-07-093045-opt.md").write_text("# opt\n")
    monkeypatch.setenv("NOTES_DIR", str(tmp_path / "from-env"))
    result = CliRunner().invoke(cli, ["list", "--notes-dir", str(other)])
    assert result.exit_code == 0, result.output
    assert "opt.md" in result.output
    assert not (tmp_path / "from-env").exists()


def test_show_by_index_prints_filename_header_and_content(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo\nbody\n")
    result = CliRunner().invoke(cli, ["show", "1"])
    assert result.exit_code == 0, result.output
    assert result.output == "2026-05-07-093045-foo.md\n\n# foo\nbody\n"


def test_show_by_filename(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo\nbody\n")
    result = CliRunner().invoke(
        cli, ["show", "2026-05-07-093045-foo.md"]
    )
    assert result.exit_code == 0, result.output
    assert result.output == "2026-05-07-093045-foo.md\n\n# foo\nbody\n"


def test_show_index_picks_newest_first(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-06-094501-old.md").write_text("# old\n")
    (tmp_path / "2026-05-07-093045-new.md").write_text("# new\n")
    result = CliRunner().invoke(cli, ["show", "1"])
    assert result.exit_code == 0, result.output
    assert "2026-05-07-093045-new.md" in result.output
    assert "# new" in result.output


def test_show_preserves_no_trailing_newline(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo")
    result = CliRunner().invoke(cli, ["show", "1"])
    assert result.exit_code == 0, result.output
    assert result.output == "2026-05-07-093045-foo.md\n\n# foo"


def test_show_index_out_of_range_exits_2(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo\n")
    result = CliRunner().invoke(cli, ["show", "99"])
    assert result.exit_code == 2
    assert "only 1 notes" in result.output


def test_show_zero_exits_2(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    (tmp_path / "2026-05-07-093045-foo.md").write_text("# foo\n")
    result = CliRunner().invoke(cli, ["show", "0"])
    assert result.exit_code == 2


def test_show_missing_filename_exits_2(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    result = CliRunner().invoke(cli, ["show", "nope.md"])
    assert result.exit_code == 2
    assert "no such note" in result.output.lower()


def test_show_path_traversal_exits_2(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    result = CliRunner().invoke(cli, ["show", "../etc/passwd"])
    assert result.exit_code == 2


def test_show_empty_dir_with_index_exits_2(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    result = CliRunner().invoke(cli, ["show", "1"])
    assert result.exit_code == 2
    assert "no notes" in result.output


def test_show_does_not_create_missing_notes_dir(tmp_path, monkeypatch):
    target = tmp_path / "does-not-exist"
    monkeypatch.setenv("NOTES_DIR", str(target))
    result = CliRunner().invoke(cli, ["show", "1"])
    assert result.exit_code == 2
    assert not target.exists()


def test_show_uses_notes_dir_option_over_env(tmp_path, monkeypatch):
    other = tmp_path / "from-option"
    other.mkdir()
    (other / "2026-05-07-093045-opt.md").write_text("# opt body\n")
    monkeypatch.setenv("NOTES_DIR", str(tmp_path / "from-env"))
    result = CliRunner().invoke(
        cli, ["show", "--notes-dir", str(other), "1"]
    )
    assert result.exit_code == 0, result.output
    assert "opt body" in result.output
    assert not (tmp_path / "from-env").exists()


def test_show_missing_argument_exits_2():
    result = CliRunner().invoke(cli, ["show"])
    assert result.exit_code == 2
