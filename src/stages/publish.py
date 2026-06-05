import os
import subprocess

from src.stages.base import BaseStage


class PublishStage(BaseStage):
    @property
    def name(self) -> str:
        return "publish"

    def run(self) -> bool:
        registry = self.config.get("registry", {})
        url = os.getenv("REGISTRY_URL", registry.get("url", ""))
        image = os.getenv("IMAGE_NAME", registry.get("image", "app"))
        tag = os.getenv("BUILD_TAG", "latest")
        username = os.getenv("REGISTRY_USERNAME", registry.get("username", "")).strip()
        password = os.getenv("REGISTRY_PASSWORD", registry.get("password", "")).strip()

        full_image = f"{url}/{image}:{tag}" if url else f"{image}:{tag}"

        # Warn if registry specified but no credentials
        if url and not (username and password):
            self.logger.warning(
                "Registry URL specified but no credentials found. "
                "Ensure 'docker login' has been run beforehand."
            )

        # Docker login (safe: uses stdin, not command-line args)
        if url and username and password:
            self.logger.info(f"Logging in to registry: {url}")
            login = subprocess.run(
                ["docker", "login", "-u", username, "--password-stdin", url],
                input=password,
                text=True,
                capture_output=True,
                check=False,
            )
            if login.returncode != 0:
                self.logger.error(login.stderr or login.stdout)
                return False

        # Verify image exists locally before push
        self.logger.info(f"Verifying image exists: {full_image}")
        inspect = subprocess.run(
            ["docker", "image", "inspect", full_image],
            capture_output=True,
            text=True,
            check=False,
        )
        if inspect.returncode != 0:
            self.logger.error(f"Image not found locally: {full_image}")
            return False

        # Push image to registry
        self.logger.info(f"Pushing image: {full_image}")
        result = subprocess.run(
            ["docker", "push", full_image],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            self.logger.error(result.stderr or result.stdout)
            return False

        self.logger.info(f"Image published: {full_image}")
        return True
