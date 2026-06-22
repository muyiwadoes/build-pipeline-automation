#!/usr/bin/env python3
"""
Config-driven pipeline core engine.
Used by both GitHub Actions and GitLab CI.
"""

import os
import subprocess
import sys
from pathlib import Path

import yaml


def run(cmd: str, check: bool = True) -> None:
    """Execute shell command with error handling."""
    print(f"\n▶ {cmd}")

    result = subprocess.run(cmd, shell=True, text=True)

    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def load_config(config_path: str) -> dict:
    """Load YAML pipeline configuration safely."""
    path = Path(config_path)

    if not path.exists():
        print(f"❌ Missing config file: {config_path}")
        sys.exit(1)

    try:
        config = yaml.safe_load(path.read_text())

        if not isinstance(config, dict):
            print("❌ Invalid config format: expected dictionary")
            sys.exit(1)

        return config

    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}")
        sys.exit(1)


def get_branch() -> str:
    """Resolve branch name across GitHub and GitLab."""
    return (
        os.getenv("GITHUB_REF", "").replace("refs/heads/", "")
        or os.getenv("CI_COMMIT_BRANCH")
        or os.getenv("CI_COMMIT_REF_NAME")
        or "unknown"
    )


def main(config_path: str = "pipeline-config.yml"):
    config = load_config(config_path)

    stages = config.get("stages", [])
    registry = config.get("registry", {})

    image_name = registry.get("image", "build-pipeline-automation")

    sha = os.getenv("GITHUB_SHA") or os.getenv("COMMIT_SHA") or "local"
    sha = sha[:7] if sha != "local" else "local"

    full_image = f"{image_name}:{sha}"

    print(f"🚀 Pipeline stages: {stages}")
    print(f"📦 Image: {image_name}")
    print(f"🔖 Tag: {sha}")
    print(f"🌿 Branch: {get_branch()}")

    # -----------------------
    # LINT
    # -----------------------
    if "lint" in stages:
        print("\n=== LINT ===")
        run("ruff check . --line-length 120")
        run("ruff format .")

    # -----------------------
    # TEST
    # -----------------------
    if "test" in stages:
        print("\n=== TEST ===")
        run("pytest tests/ -v")

    # -----------------------
    # BUILD
    # -----------------------
    if "build" in stages:
        print("\n=== BUILD ===")
        run(f"docker build -t {full_image} .")

        print("\n=== SMOKE TEST ===")
        run(f"docker run --rm -e PYTHONPATH=. {full_image} python -c \"print('OK')\"")

    # -----------------------
    # PUBLISH GATE (CI SAFE)
    # -----------------------
    if "publish" in stages:
        print("\n=== PUBLISH ===")

        is_ci = os.getenv("CI") == "true"
        branch = get_branch()

        if is_ci and branch == "main":
            print("✅ Publish allowed (CI main branch)")
        else:
            print("⏭️ Publish skipped (not CI main branch)")

    print("\n✅ Pipeline complete")


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "pipeline-config.yml"
    main(config_file)
