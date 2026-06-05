from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from src.stages.build import BuildStage
from src.stages.lint import LintStage
from src.stages.publish import PublishStage
from src.stages.test import TestStage


@pytest.fixture
def config():
    return {
        "registry": {
            "url": "ghcr.io/my-org",
            "image": "test-app",
            "username": "testuser",
            "password": "testpass",
        }
    }


# -------------------
# LintStage (Ruff-based)
# -------------------

def test_lint_passes_when_both_checks_succeed(config):
    """Ruff lint and format checks both pass."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert LintStage(config).run() is True
        assert mock_run.call_count == 2  # ruff check + ruff format


def test_lint_fails_when_check_fails(config):
    """Ruff lint check fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="E501", stderr="")
        assert LintStage(config).run() is False


def test_lint_fails_when_format_fails(config):
    """Ruff format check fails."""
    results = [
        MagicMock(returncode=0, stdout="", stderr=""),  # ruff check passes
        MagicMock(returncode=1, stdout="", stderr="format issues"),
    ]
    with patch("subprocess.run", side_effect=results):
        assert LintStage(config).run() is False


# -------------------
# TestStage
# -------------------

def test_test_stage_passes(config):
    """Pytest succeeds."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert TestStage(config).run() is True


def test_test_stage_fails(config):
    """Pytest fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert TestStage(config).run() is False


# -------------------
# BuildStage
# -------------------

def test_build_stage_passes(config):
    """Docker build succeeds."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        assert BuildStage(config).run() is True


def test_build_stage_fails(config):
    """Docker build fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error: no Dockerfile")
        assert BuildStage(config).run() is False


def test_build_stage_uses_env_override(config, monkeypatch):
    """Build respects IMAGE_NAME and BUILD_TAG env vars."""
    monkeypatch.setenv("IMAGE_NAME", "custom-image")
    monkeypatch.setenv("BUILD_TAG", "v1.0.0")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        BuildStage(config).run()

        cmd = mock_run.call_args[0][0]
        assert "custom-image:v1.0.0" in cmd


# -------------------
# PublishStage
# -------------------

def test_publish_stage_passes(config):
    """Docker push succeeds."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        assert PublishStage(config).run() is True
        assert mock_run.call_count >= 2  # login + inspect + push


def test_publish_stage_fails_if_image_not_found(config):
    """Publish fails if image doesn't exist locally."""
    with patch("subprocess.run") as mock_run:
        # image inspect fails
        mock_run.return_value = MagicMock(returncode=1, stderr="")
        assert PublishStage(config).run() is False


def test_publish_stage_fails_if_push_fails(config):
    """Publish fails if docker push fails."""
    results = [
        MagicMock(returncode=0, stderr=""),  # login succeeds
        MagicMock(returncode=0, stderr=""),  # image inspect succeeds
        MagicMock(returncode=1, stderr="auth failed"),  # push fails
    ]
    with patch("subprocess.run", side_effect=results):
        assert PublishStage(config).run() is False


def test_publish_stage_logs_in_with_credentials(config):
    """Publish attempts docker login if credentials provided."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        PublishStage(config).run()

        # Check that login was called with --password-stdin
        login_call = mock_run.call_args_list[0][0][0]
        assert "docker" in login_call
        assert "login" in login_call
        assert "--password-stdin" in login_call


def test_publish_stage_skips_login_without_credentials(config):
    """Publish skips login if no credentials."""
    config = deepcopy(config)
    config["registry"]["username"] = ""
    config["registry"]["password"] = ""

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        PublishStage(config).run()

        # Should have inspect + push, NOT login
        assert mock_run.call_count == 2


def test_publish_stage_uses_env_override(config, monkeypatch):
    """Publish respects REGISTRY_URL and IMAGE_NAME env vars."""
    monkeypatch.setenv("REGISTRY_URL", "docker.io")
    monkeypatch.setenv("IMAGE_NAME", "myapp")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        PublishStage(config).run()

        # Last call should be push
        push_cmd = mock_run.call_args_list[-1][0][0]
        assert "docker.io/myapp:latest" in push_cmd
