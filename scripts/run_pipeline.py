#!/usr/bin/env python3
"""
Config-driven pipeline entrypoint.
"""

import importlib
import sys


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "pipeline-config.yml"

    module = importlib.import_module("src.stages.pipeline")
    module.main(config_file)


if __name__ == "__main__":
    main()
