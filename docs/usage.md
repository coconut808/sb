# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Running

Bare invocation prints the help screen with the available subcommands:

```bash
uv run second_brain
uv run python -m second_brain
```

### `second_brain new "<text>"`

Save a quick thought as a plain markdown file under `$NOTES_DIR`:

```bash
uv run second_brain new "My brilliant idea about caching"
# /Users/me/second_brain/2026-05-07-093045-my-brilliant-idea-about-caching.md
```

The command prints the absolute path of the file it wrote, so you can pipe it
to `$EDITOR` or another tool. The file contains a single H1 with your text:

```markdown
# My brilliant idea about caching
```

Filenames use `YYYY-MM-DD-HHMMSS-<slug>.md`, where the slug is the lowercased,
ASCII-folded text with non-word characters stripped.

### `second_brain list`

List saved notes, newest first:

```bash
uv run second_brain list
# Notes in /Users/me/second_brain:
#
#   1. 2026-05-07-093045-my-brilliant-idea.md
#   2. 2026-05-06-201233-grocery-list.md
#   3. 2026-05-06-094501-meeting-notes.md
```

Only top-level `*.md` files are listed; subdirectories and other extensions are
ignored. Sort order is reverse-lexical, which matches "newest first" because of
the `YYYY-MM-DD-HHMMSS` filename prefix.

If the directory is missing it is created (matching `new`'s behavior) and an
empty-list placeholder is shown:

```
Notes in /Users/me/second_brain:

  (no notes yet)
```

The exit code is always `0` — an empty notes directory is not an error.

### `second_brain hello`

Legacy smoke test — prints the greeting through the configured logger.

## Environment Variables

| Variable    | Default            | Description                                   |
|-------------|--------------------|-----------------------------------------------|
| `LOG_LEVEL` | `INFO`             | Console log level (DEBUG, INFO, …)            |
| `LOG_FILE`  | `app.log`          | Path to the log file                          |
| `NOTES_DIR` | `~/second_brain`   | Directory where `second_brain new` saves notes and `list` reads from |

Copy `.env.example` to `.env` for development defaults, then run with `uv run --env-file .env`.

`NOTES_DIR` can also be overridden per-call with `--notes-dir`, on either `new`
or `list`:

```bash
uv run second_brain new --notes-dir /tmp/scratch "throwaway thought"
uv run second_brain list --notes-dir /tmp/scratch
```

## Logging

Logs are written in a compact format, applied identically to both stderr and the log file:

```
2026-05-07 12:34:56 | INF | second_brain.app:hello:53 | Hello from second_brain!
```

- Timestamp is second-resolution (no milliseconds)
- Level is a 3-letter abbreviation: `DBG`, `INF`, `WRN`, `ERR`, `CRT`
- Fields are pipe-separated

The format itself is fixed; environment variables only control the level (`LOG_LEVEL`) and destination (`LOG_FILE`).
