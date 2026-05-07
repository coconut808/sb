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
