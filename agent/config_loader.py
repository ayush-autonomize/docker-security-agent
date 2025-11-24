"""Simple configuration loader for agent YAML files."""
import yaml
from pathlib import Path
from typing import Any, Dict


def load_yaml(path: str) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Raises FileNotFoundError if the file does not exist or yaml.YAMLError on parse errors.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
