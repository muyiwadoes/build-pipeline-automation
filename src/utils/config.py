import os
from pathlib import Path

import yaml


def load_config(config_path: str = "pipeline-config.yml") -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    _apply_env_overrides(config)
    return config


def _apply_env_overrides(config: dict) -> None:
    """Allow environment variables to override registry settings."""
    registry = config.setdefault("registry", {})
    if url := os.getenv("REGISTRY_URL"):
        registry["url"] = url
    if image := os.getenv("IMAGE_NAME"):
        registry["image"] = image