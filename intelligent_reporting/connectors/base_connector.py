from abc import ABC, abstractmethod
import polars as pl

class BaseConnector(ABC):
    """
    Generic interface for any data source
    """
    allowed_options: set[str] = set()

    @abstractmethod
    def load(self) -> pl.DataFrame:
        pass