from abc import ABC, abstractmethod
import polars as pl

class BaseConnector(ABC):
    """
    Generic interface for any data source
    """

    @abstractmethod
    def load(self) -> pl.DataFrame:
        pass