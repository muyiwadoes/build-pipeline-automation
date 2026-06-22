#!/usr/bin/env python3
"""
Config-driven pipeline entrypoint.

Delegates execution to src/stages/pipeline.py.
"""

import sys
import importlib


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "pipeline-config.yml"

    # Import module dynamically (safe for CI + packaging)
    module = importlib.import_module("src.stages.pipeline")

    # Call its main() function
    module.main(config_file)


if __name__ == "__main__":
    main()