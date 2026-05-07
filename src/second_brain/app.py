import os
import sys
from pathlib import Path

import click
from loguru import logger

from second_brain.notes import list_notes, read_note, write_note


_LEVEL_ABBR = {
    "DEBUG": "DBG",
    "INFO": "INF",
    "WARNING": "WRN",
    "ERROR": "ERR",
    "CRITICAL": "CRT",
}


def _log_format(record):
    abbr = _LEVEL_ABBR.get(record["level"].name, record["level"].name[:3])
    return (
        f"<green>{{time:YYYY-MM-DD HH:mm:ss}}</green> | <level>{abbr}</level> | "
        f"<cyan>{{name}}</cyan>:<cyan>{{function}}</cyan>:<cyan>{{line}}</cyan> | "
        f"<level>{{message}}</level>\n{{exception}}"
    )


def configure_logging():
    """Configure loguru for console and file logging.

    Removes the default handler and sets up:
    - stderr handler at LOG_LEVEL (default: INFO, configurable via env var)
    - File handler at DEBUG level writing to LOG_FILE (default: app.log)
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_file = os.environ.get("LOG_FILE", "app.log")
    logger.remove()
    logger.add(sys.stderr, level=log_level, format=_log_format)
    logger.add(log_file, level="DEBUG", format=_log_format, rotation="50 KB", retention=1)


@click.group()
def cli():
    """second-brain — quick-capture notes from the terminal."""


@cli.command()
def hello():
    """Print greeting (legacy smoke test)."""
    configure_logging()
    logger.info("Hello from second_brain!")


@cli.command(name="new")
@click.argument("text")
@click.option(
    "--notes-dir",
    envvar="NOTES_DIR",
    default="~/second_brain",
    show_default=True,
    help="Directory where notes are saved. Reads NOTES_DIR if set.",
)
def new_note(text: str, notes_dir: str):
    """Save TEXT as a quick-thought markdown file."""
    path = write_note(text, notes_dir)
    click.echo(str(path))


@cli.command(name="list")
@click.option(
    "--notes-dir",
    envvar="NOTES_DIR",
    default="~/second_brain",
    show_default=True,
    help="Directory where notes are read from. Reads NOTES_DIR if set.",
)
def list_notes_cmd(notes_dir: str):
    """Show saved notes, newest first."""
    directory = Path(notes_dir).expanduser()
    notes = list_notes(notes_dir)
    click.echo(f"Notes in {directory}:")
    click.echo()
    if not notes:
        click.echo("  (no notes yet)")
        return
    width = len(str(len(notes)))
    for i, path in enumerate(notes, start=1):
        click.echo(f"  {i:>{width}}. {path.name}")


@cli.command(name="show")
@click.argument("note", type=click.STRING)
@click.option(
    "--notes-dir",
    envvar="NOTES_DIR",
    default="~/second_brain",
    show_default=True,
    help="Directory where notes are read from. Reads NOTES_DIR if set.",
)
def show_note(note: str, notes_dir: str):
    """Print a note's contents. NOTE is a list index or a filename."""
    try:
        path, content = read_note(notes_dir, note)
    except (ValueError, IndexError, FileNotFoundError) as exc:
        raise click.BadParameter(str(exc), param_hint="NOTE") from exc
    click.echo(path.name)
    click.echo()
    click.echo(content, nl=False)
