import subprocess

from src.stages.base import BaseStage


class LintStage(BaseStage):
    @property
    def name(self) -> str:
        return "lint"

    def run(self) -> bool:
        return self._run_ruff_check() and self._run_ruff_format()

    def _run_ruff_check(self) -> bool:
        self.logger.info("Running Ruff lint checks...")
        result = subprocess.run(
            ["ruff", "check", "src/", "tests/"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            self.logger.error(f"Ruff lint errors:\n{result.stdout}")
            return False
        self.logger.info("Ruff lint checks passed")
        return True

    def _run_ruff_format(self) -> bool:
        self.logger.info("Running Ruff format check...")
        result = subprocess.run(
            ["ruff", "format", "--check", "src/", "tests/"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            self.logger.error(
                f"Ruff formatting issues detected:\n{result.stdout or result.stderr}"
            )
            return False
        self.logger.info("Ruff format check passed")
        return True
