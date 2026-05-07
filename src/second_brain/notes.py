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


def read_note(notes_dir: str, note_ref: str) -> tuple[Path, str]:
    """Resolve note_ref (1-based index or filename) and return (path, content).

    Read-only: never creates notes_dir.
    """
    if not note_ref or not note_ref.strip():
        raise ValueError("note reference is empty")
    if "/" in note_ref or "\\" in note_ref or ".." in note_ref:
        raise ValueError(f"invalid note reference: {note_ref!r}")

    directory = Path(notes_dir).expanduser()
    if note_ref.isdigit():
        index = int(note_ref)
        notes = (
            sorted(directory.glob("*.md"), reverse=True)
            if directory.is_dir()
            else []
        )
        if index < 1 or index > len(notes):
            if not notes:
                raise IndexError(f"no notes in {directory}")
            raise IndexError(
                f"note {index} not found (only {len(notes)} notes)"
            )
        path = notes[index - 1]
    else:
        path = directory / note_ref
        if not path.is_file():
            raise FileNotFoundError(f"no such note: {note_ref}")

    return path, path.read_text()
