#!/usr/bin/env python3
"""
Config-driven pipeline runner.
Works both locally and in CI (GitHub Actions).
"""

import subprocess
import sys
import os
from pathlib import Path

import yaml


def run(cmd: str, check: bool = True) -> None:
    """Run a shell command with nice output."""
    print(f"\n▶ {cmd}")
    result = subprocess.run(cmd, shell=True, text=True)

    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def load_config(config_path: str) -> dict:
    """Load and validate pipeline config."""
    path = Path(config_path)
    if not path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    try:
        config = yaml.safe_load(path.read_text())
        if not isinstance(config, dict):
            print("❌ Invalid config: root must be a dictionary")
            sys.exit(1)
        return config
    except yaml.YAMLError as e:
        print(f"❌ Failed to parse YAML config: {e}")
        sys.exit(1)


def main(config_path: str = "pipeline-config.yml"):
    config = load_config(config_path)

    stages: list[str] = config.get("stages", [])
    registry = config.get("registry", {})

    print(f"🚀 Starting pipeline with stages: {stages}")
    print(f"📦 Image name: {registry.get('image', 'build-pipeline-automation')}")

    # Environment-aware variables
    github_sha = os.getenv("GITHUB_SHA") or os.getenv("COMMIT_SHA") or "local"
    image_name = registry.get("image", "build-pipeline-automation")
    full_image = f"{image_name}:{github_sha}"

    # -----------------------
    # LINT
    # -----------------------
    if "lint" in stages:
        print("\n=== LINT ===")
        run("ruff check .")
        run("ruff format --check .")

    # -----------------------
    # TEST
    # -----------------------
    if "test" in stages:
        print("\n=== TEST ===")
        run("pytest tests/ --cov=src --cov-report=xml:coverage.xml -v")

    # -----------------------
    # BUILD
    # -----------------------
    if "build" in stages:
        print("\n=== BUILD ===")
        print(f"Building image: {full_image}")
        run(f"docker build -t {full_image} .")

        # Optional smoke test
        print("\n=== SMOKE TEST ===")
        run(
            f"docker run --rm -e PYTHONPATH=. {full_image} "
            f'python -c "from src.pipeline import Pipeline; print(\'✅ Smoke test passed\')"'
        )

    # -----------------------
    # PUBLISH (only in CI on main branch)
    # -----------------------
    if "publish" in stages:
        print("\n=== PUBLISH ===")
        if os.getenv("GITHUB_ACTIONS") == "true" and os.getenv("GITHUB_REF") == "refs/heads/main":
            print("✅ Running in CI on main branch → Publish stage active")
            # Future: Add push logic here or call a separate publish script
        else:
            print("⏭️  Publish stage skipped (only runs on main branch in CI)")

    print("\n✅ Pipeline completed successfully!")


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "pipeline-config.yml"
    main(config_file)