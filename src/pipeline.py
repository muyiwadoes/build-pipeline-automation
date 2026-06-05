import sys

from src.stages.build import BuildStage
from src.stages.lint import LintStage
from src.stages.publish import PublishStage
from src.stages.test import TestStage
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

STAGE_MAP = {
    "lint": LintStage,
    "test": TestStage,
    "build": BuildStage,
    "publish": PublishStage,
}


class Pipeline:
    def __init__(self, config_path: str = "pipeline-config.yml"):
        self.config = load_config(config_path)
        self.stages = self._build_stages()

    def _build_stages(self):
        return [
            STAGE_MAP[name](self.config)
            for name in self.config.get("stages", [])
            if name in STAGE_MAP
        ]

    def run(self) -> bool:
        logger.info("Pipeline started")
        for stage in self.stages:
            logger.info(f"Running stage: {stage.name}")
            try:
                success = stage.run()
            except Exception as e:
                logger.error(f"Stage '{stage.name}' crashed: {e}")
                return False
            if not success:
                logger.error(f"Stage '{stage.name}' failed — aborting pipeline")
                return False
        logger.info("Pipeline completed successfully")
        return True


if __name__ == "__main__":
    pipeline = Pipeline()
    sys.exit(0 if pipeline.run() else 1)
