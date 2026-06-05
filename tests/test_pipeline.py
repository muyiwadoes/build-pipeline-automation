from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline import Pipeline


@pytest.fixture
def mock_config():
    return {
        "stages": ["lint", "test"],
        "cache": {"enabled": True},
        "registry": {"url": "", "image": "test-app"},
    }


def test_pipeline_runs_all_stages(mock_config):
    """Pipeline should run all stages in order."""
    with patch("src.pipeline.load_config", return_value=mock_config):
        pipeline = Pipeline()
        for stage in pipeline.stages:
            stage.run = MagicMock(return_value=True)
        
        assert pipeline.run() is True
        for stage in pipeline.stages:
            stage.run.assert_called_once()


def test_pipeline_aborts_on_first_failure(mock_config):
    """Pipeline should abort when a stage fails."""
    with patch("src.pipeline.load_config", return_value=mock_config):
        pipeline = Pipeline()
        pipeline.stages[0].run = MagicMock(return_value=False)
        pipeline.stages[1].run = MagicMock(return_value=True)
        
        assert pipeline.run() is False
        pipeline.stages[0].run.assert_called_once()
        pipeline.stages[1].run.assert_not_called()


def test_pipeline_builds_correct_stage_names(mock_config):
    """Pipeline should instantiate only configured stages."""
    with patch("src.pipeline.load_config", return_value=mock_config):
        pipeline = Pipeline()
        assert [stage.name for stage in pipeline.stages] == ["lint", "test"]


def test_pipeline_skips_unknown_stages(mock_config):
    """Pipeline should skip unrecognized stage names."""
    config = deepcopy(mock_config)
    config["stages"] = ["lint", "unknown_stage", "test"]
    
    with patch("src.pipeline.load_config", return_value=config):
        pipeline = Pipeline()
        assert len(pipeline.stages) == 2
        assert [s.name for s in pipeline.stages] == ["lint", "test"]


def test_pipeline_with_no_stages(mock_config):
    """Pipeline should succeed gracefully with no stages."""
    config = deepcopy(mock_config)
    config["stages"] = []
    
    with patch("src.pipeline.load_config", return_value=config):
        pipeline = Pipeline()
        assert pipeline.run() is True