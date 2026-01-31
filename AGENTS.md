# Repository Guidelines

## Project Structure & Module Organization
- `main.py` is the current application entry point.
- `pyproject.toml` defines project metadata and Python requirements.
- `README.md` is reserved for project overview and usage notes (currently empty).
- No dedicated `src/`, `tests/`, or asset directories exist yet.

## Build, Test, and Development Commands
- `python main.py` — run the program locally.
- `python -m venv .venv` — create a virtual environment.
- `source .venv/bin/activate` — activate the virtual environment on macOS/Linux.
- `python -V` — confirm Python 3.12+ (required by `pyproject.toml`).

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation.
- Use `snake_case` for functions and variables; `PascalCase` for classes.
- Keep module files small and focused; prefer one responsibility per module.
- There are no configured formatters or linters yet; add tools like `ruff` or `black` only if the project adopts them.

## Testing Guidelines
- No testing framework is configured.
- If tests are added, prefer `pytest` and place files under `tests/` using `test_*.py` naming.
- Document any required fixtures or test data in `README.md` when introduced.

## Commit & Pull Request Guidelines
- Git history is minimal (only “Initialize Repo”), so no commit message convention is established yet.
- Use clear, imperative commit messages (e.g., `Add CLI entry point`).
- Pull requests should include a brief description, rationale, and testing notes (or “not tested”).

## Security & Configuration Tips
- Do not commit secrets or local config files.
- If configuration is needed later, prefer `.env` plus a checked-in `.env.example`.
