# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Running

Via the CLI entrypoint:

```bash
uv run second_brain                          # production defaults
uv run --env-file .env second_brain          # dev settings
```

Or as a Python module:

```bash
uv run python -m second_brain
```

## Environment Variables

| Variable    | Default    | Description                          |
|-------------|------------|--------------------------------------|
| `LOG_LEVEL` | `INFO`     | Console log level (DEBUG, INFO, …)   |
| `LOG_FILE`  | `app.log`  | Path to the log file                 |

Copy `.env.example` to `.env` for development defaults, then run with `uv run --env-file .env`.

## Logging

Logs are written in a compact format, applied identically to both stderr and the log file:

```
2026-05-07 12:34:56 | INF | second_brain.app:main:42 | Hello from second_brain!
```

- Timestamp is second-resolution (no milliseconds)
- Level is a 3-letter abbreviation: `DBG`, `INF`, `WRN`, `ERR`, `CRT`
- Fields are pipe-separated

The format itself is fixed; environment variables only control the level (`LOG_LEVEL`) and destination (`LOG_FILE`).
