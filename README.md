# second-brain

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd second-brain
uv sync
```

## Usage

Bare invocation prints the help screen:

```bash
uv run second_brain
uv run python -m second_brain
```

Save a quick thought:

```bash
uv run second_brain new "My brilliant idea about caching"
```

The note is written as a plain markdown file under `$NOTES_DIR` (default `~/second_brain`), and the absolute path is printed to stdout.

The legacy greeting is preserved as `second_brain hello` (smoke test).

## Environment Variables

Copy `.env.example` to `.env` for development defaults:

```bash
cp .env.example .env
```

Note: `uv run --env-file .env` loads the dev environment explicitly — there is no auto-loading.

| Variable    | Default          | Description                                                  |
|-------------|------------------|--------------------------------------------------------------|
| `LOG_LEVEL` | `INFO`           | Console log level. Set to `DEBUG` in `.env` for verbose output. |
| `LOG_FILE`  | `app.log`        | Path to the log file.                                         |
| `NOTES_DIR` | `~/second_brain` | Directory where `second_brain new` saves notes.               |

## Logging

Both stderr and the log file use the same compact format:

```
2026-05-07 12:34:56 | INF | second_brain.app:hello:53 | Hello from second_brain!
```

Levels are abbreviated to three letters (`DBG`, `INF`, `WRN`, `ERR`, `CRT`) and fields are pipe-separated.

## Testing

Run the test suite:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov
```

## Documentation

Preview docs locally:

```bash
uv run python scripts/serve_docs.py
```

Build static docs:

```bash
uv run mkdocs build
```
