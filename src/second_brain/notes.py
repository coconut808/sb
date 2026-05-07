import re
import unicodedata
from datetime import datetime
from pathlib import Path


_SLUG_MAX = 60


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text[:_SLUG_MAX].strip("-") or "note"


def write_note(text: str, notes_dir: str, *, now: datetime | None = None) -> Path:
    when = now or datetime.now()
    directory = Path(notes_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    directory = directory.resolve()
    path = directory / f"{when:%Y-%m-%d-%H%M%S}-{slugify(text)}.md"
    path.write_text(f"# {text}\n")
    return path


def list_notes(notes_dir: str) -> list[Path]:
    """Return *.md files in notes_dir, newest first. Creates the dir if missing."""
    directory = Path(notes_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    return sorted(directory.glob("*.md"), reverse=True)
