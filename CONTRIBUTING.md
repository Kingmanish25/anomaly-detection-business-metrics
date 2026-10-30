# Contributing to anomaly-detection-business-metrics

Thank you for your interest in contributing!

## Getting Started

1. **Fork** the repository and clone your fork.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your values.
4. Start infrastructure services:
   ```bash
   docker compose up -d postgres redis
   ```
5. Run the test suite:
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

- Branch: `feat/<description>`, `fix/<issue>`, `chore/<topic>`
- All commits must pass `ruff check .` and `mypy .` locally.
- Write tests in `tests/` for every change.
- Open a Pull Request against `main`.

## Code Style

- Formatter / linter: **Ruff** (`ruff check . --fix && ruff format .`)
- Type checker: **mypy** (`mypy src/`)
- Security scan: **Bandit** (`bandit -r src/ -x tests -ll`)

## Reporting Issues

Open a GitHub Issue with a clear title, steps to reproduce, and expected vs actual behaviour.
