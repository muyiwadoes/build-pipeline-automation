import os
import subprocess

from src.stages.base import BaseStage


class BuildStage(BaseStage):
    @property
    def name(self) -> str:
        return "build"

    def run(self) -> bool:
        registry = self.config.get("registry", {})

        image = os.getenv("IMAGE_NAME", registry.get("image", "app"))
        tag = os.getenv("BUILD_TAG", "latest")

        full_tag = f"{image}:{tag}"

        self.logger.info(f"Building Docker image: {full_tag}")

        result = subprocess.run(
            ["docker", "build", "-t", full_tag, "."],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            self.logger.error(f"Docker build failed:\n{result.stderr}")
            return False

        self.logger.info(f"Image built successfully: {full_tag}")
        return True
