# jot-cli

A terminal-based task execution tool for focused work. Jot helps you maintain single-task focus with a persistent monitor window, behavioral reinforcement, and accomplishment tracking.

## Features

- **Single-Task Focus**: Enforce one active task at a time
- **Persistent Monitor**: Terminal UI window showing current task and daily progress
- **Behavioral Reinforcement**: Streaks, celebrations, and engagement features
- **Task History**: Complete audit trail of all task activity
- **Simple CLI**: Intuitive commands for task management

## Requirements

- **Python 3.13+** (required for performance improvements and modern type hints)
- Poetry 2.1+ for dependency management

## Installation

### Development Setup

```bash
# Clone the repository
git clone https://github.com/djudge/jot-cli.git
cd jot-cli

# Install dependencies
poetry install

# Verify installation
poetry run jot --help
```

### Platform Notes

- **Windows**: CLI command appears as `jot.cmd` (Poetry wrapper)
- **macOS/Linux**: CLI command is `jot`

## Usage

```bash
# Show help
poetry run jot --help

# Future commands (not yet implemented):
# jot add "Task description"     - Add a new task
# jot done                        - Complete current task
# jot status                      - Show current task
# jot monitor                     - Launch persistent monitor window
```

## Development

### Technology Stack

- **Python 3.13+**: Core language
- **Typer 0.21.1**: CLI framework
- **Rich 14.3.1**: Terminal formatting
- **Textual 7.3.0**: TUI monitor window
- **Pydantic 2.12.5**: Data validation
- **SQLite**: Task persistence

### Code Quality Tools

```bash
# Run tests
poetry run pytest

# Run tests with coverage (80% minimum)
poetry run pytest --cov

# Type checking
poetry run mypy src/

# Linting
poetry run ruff check src/

# Code formatting
poetry run black src/
```

### Project Structure

```
jot-cli/
├── src/
│   └── jot/
│       ├── __init__.py       # Package initialization
│       └── cli.py            # CLI entry point
├── tests/                    # Test suite
├── pyproject.toml           # Poetry configuration
└── README.md                # This file
```

## Architecture

Jot follows a clean MVC architecture:
- **Model**: SQLite database with Pydantic domain models
- **View**: Rich (CLI output) + Textual (TUI monitor)
- **Controller**: Typer command handlers

See `_bmad-output/planning-artifacts/architecture.md` for detailed design decisions.

## Contributing

This project is in active development. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run code quality checks (ruff, mypy, black)
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Status

🚧 **Active Development** - Core features in progress

Current sprint: Epic 1 (Project Foundation & Development Infrastructure)
