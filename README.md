# natural-code

A Python project using uv for dependency management.

## Setup

### Prerequisites
- Python 3.13+
- uv package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd natural-code

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Run the project
uv run python main.py

# Run tests
uv run pytest
```

## Development

```bash
# Add dependencies
uv add requests

# Add dev dependencies
uv add --dev pytest black ruff

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```