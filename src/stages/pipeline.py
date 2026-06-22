#!/usr/bin/env python3
"""
Config-driven pipeline runner.
Works locally and in CI (GitHub Actions).
"""

import subprocess
import sys
import os
from pathlib import Path

import yaml


def run(cmd: str, check: bool = True) -> None:
    """Run a shell command with clear output."""
    print(f"\n▶ {cmd}")

    result = subprocess.run(cmd, shell=True, text=True)

    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def load_config(config_path: str) -> dict:
    """Load and validate YAML config."""
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
        print(f"❌ YAML parsing error: {e}")
        sys.exit(1)


def main(config_path: str = "pipeline-config.yml"):
    config = load_config(config_path)

    stages = config.get("stages", [])
    registry = config.get("registry", {})

    print(f"🚀 Pipeline stages: {stages}")
    print(f"📦 Registry image: {registry.get('image', 'build-pipeline-automation')}")

    # -----------------------
    # SAFE SHA HANDLING
    # -----------------------
    github_sha = (
        os.getenv("GITHUB_SHA")
        or os.getenv("COMMIT_SHA")
        or "local"
    )

    github_sha = github_sha[:7] if github_sha != "local" else "local"

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

        run("docker version")

        run(f"docker build -t {full_image} .")

        print("\n=== SMOKE TEST ===")
        run(
            f"docker run --rm -e PYTHONPATH=. {full_image} "
            f'python -c "import src.pipeline; print(\'✅ Smoke test passed\')"'
        )

    # -----------------------
    # PUBLISH (CI-safe guard only)
    # -----------------------
    if "publish" in stages:
        print("\n=== PUBLISH ===")

        is_ci = os.getenv("GITHUB_ACTIONS") == "true"
        is_main = os.getenv("GITHUB_REF") == "refs/heads/main"
        is_push = os.getenv("GITHUB_EVENT_NAME") == "push"

        if is_ci and is_push and is_main:
            print("✅ Publish allowed (CI main branch push)")
        else:
            print("⏭️ Publish skipped (not eligible CI context)")

    print("\n✅ Pipeline completed successfully!")


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "pipeline-config.yml"
    main(config_file)