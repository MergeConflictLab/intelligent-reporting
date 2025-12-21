from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Agent(ABC):
    """
    Abstract base class for all agents.
    """

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """
        Execute the agent's main logic.
        """
        pass
