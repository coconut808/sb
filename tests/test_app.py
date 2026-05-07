import os
import re

from loguru import logger

from second_brain.app import configure_logging, main


LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| "
    r"(DBG|INF|WRN|ERR|CRT) \| "
    r"[\w.]+:\w+:\d+ \| "
    r".*$",
    re.MULTILINE,
)


def test_main_logs_greeting(capfd):
    main()
    captured = capfd.readouterr()
    assert "Hello from second_brain!" in captured.err


def test_log_format_uses_pipe_separator_and_3letter_level(capfd):
    main()
    captured = capfd.readouterr()
    matching = [line for line in captured.err.splitlines() if LINE_RE.match(line)]
    assert any("INF" in line and "Hello from second_brain!" in line for line in matching)
    # No millisecond fragment between :ss and the first pipe
    assert not re.search(r":\d{2}\.\d", captured.err)
    # Old dash-before-message format must not appear
    assert " - Hello from second_brain!" not in captured.err


def test_log_format_applied_to_file_handler():
    main()
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
    # Force flush by removing handlers
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
