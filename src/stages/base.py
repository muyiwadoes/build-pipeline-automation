from abc import ABC, abstractmethod
from typing import Any

from src.utils.logger import get_logger


class BaseStage(ABC):
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable stage name."""

    @abstractmethod
    def run(self) -> bool:
        """Execute the stage and return True on success."""
