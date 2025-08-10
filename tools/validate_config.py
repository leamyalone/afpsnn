import pathlib
import sys

import yaml


def validate_yaml(path: pathlib.Path) -> bool:
    """Load a YAML file to ensure it is syntactically valid."""
    with path.open("r") as f:
        yaml.safe_load(f)
    return True


def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    try:
        # Validate default configs
        validate_yaml(root / "configs" / "features.yaml")
        validate_yaml(root / "configs" / "sim_config.yaml")
        # Validate smoke config if present
        smoke_path = root / "configs" / "sim_config.smoke.yaml"
        if smoke_path.exists():
            validate_yaml(smoke_path)
    except Exception as e:
        print(f"Config validation error: {e}")
        sys.exit(1)
    print("Config validation OK.")


if __name__ == "__main__":
    main()
