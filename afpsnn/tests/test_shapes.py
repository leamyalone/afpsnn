from pathlib import Path


def test_repo_layout():
    """Ensure essential project directories are present."""
    root = Path(__file__).resolve().parents[1]
    required = ["models", "configs", "src"]
    for name in required:
        path = root / name
        assert path.exists(), f"Expected '{name}' to exist at {path}"
