import subprocess

from src.stages.base import BaseStage


class TestStage(BaseStage):
    @property
    def name(self) -> str:
        return "test"

    def run(self) -> bool:
        self.logger.info("Running pytest...")
        result = subprocess.run(
            [
                "pytest",
                "tests",
                "--cov=src",
                "--cov-report=term-missing",
                "-v",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Only log output on failure (avoid log clutter)
        if result.returncode != 0:
            self.logger.error("Tests failed")
            if result.stdout:
                self.logger.error(f"Test output:\n{result.stdout}")
            if result.stderr:
                self.logger.warning(f"Stderr:\n{result.stderr}")
            return False

        self.logger.info("All tests passed")
        return True
