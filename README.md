# MedianView

A simple web application to upload an image, apply a deterministic 3x3 median filter, and view the original and filtered images side-by-side.

## Getting Started

### Prerequisites
- Python 3.12+
- `uv`

### Installation & Development
```bash
uv sync --extra dev
```

### Running Quality Gates
```bash
uv run pytest
uv run ruff check .
uv run mypy src tests
```

### Running the App
```bash
uv run python -m medianview.app
```
