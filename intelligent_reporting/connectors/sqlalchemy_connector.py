import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy import text, inspect
import polars as pl
from .base_connector import BaseConnector
from .registry import register_db
from ..expection import *
from sqlalchemy.exc import (
    NoSuchModuleError,
    OperationalError,
    ProgrammingError,
    IntegrityError,
    DBAPIError,
)

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@register_db
class SQLConnector(BaseConnector):
    def __init__(self, *, db_url: str = None):
        """
        Only one of db_url or engine should be provided
        """
        if not db_url:
            raise ConfigurationError(
                "Please provide the database connection string (db_url)"
            )
        self.db_url = db_url
        self.engine : Engine | None = None

    def _get_engine(self) -> Engine:
        """
        returns an SQLAlchemy engine
        """
        if self.engine is None:
            try:
                self.engine = sa.create_engine(self.db_url)
            except Exception as e:
                raise DataLoadingError(
                    "Failed to create SQLAlchemy engine"
                ) from e
        return self.engine
    
    def _sanity_check_connection(self, engine: Engine):
        """
        Check connection sanity
        """
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except NoSuchModuleError as e:
            raise MissingDialectOrDriverError(
                "Database dialect or driver is not installed or invalid"
            ) from e

        except OperationalError as e:
            orig = getattr(e, "orig", None)
            msg = str(orig or e).lower()

            if any(k in msg for k in ["authentication", "password", "login failed", "access denied"]):
                raise AuthenticationError(
                    "Database authentication failed, password is not correct."
                ) from None

            if any(k in msg for k in ["could not connect", "connection refused", "timeout", "host"]):
                raise NetworkError(
                    "Cannot reach database host or port."
                ) from e

            if any(k in msg for k in ["does not exist", "unknown database", "invalid catalog name"]):
                raise DatabaseNotFoundError(
                    "Target database does not exist."
                ) from e

            raise UnknownDatabaseError(
                "Operational database error."
            ) from e

        except ProgrammingError as e:
            raise PermissionError(
                "Database operation not permitted."
            ) from e

        except IntegrityError as e:
            raise UnknownDatabaseError(
                "Database integrity error."
            ) from e

        except DBAPIError as e:
            raise UnknownDatabaseError(
                "Unexpected database error."
            ) from e
            

    def _sanity_check_table(self, engine: Engine, table: str):
        """
        Check table sanity
        """
        inspector = inspect(engine)

        if not inspector.has_table(table):
            raise DataLoadingError(
                f"Table '{table}' does not exist in the database"
            )

        columns = inspector.get_columns(table)
        if not columns:
            raise DataLoadingError(
                f"Table '{table}' has no columns"
            )

    def load(self, *, table: str | None = None) -> Engine:
        """
        Load data from the database
        """
        # configuration validation 
        if not table:
            raise ConfigurationError(
                "Please provide the source table name"
            )

        engine = self._get_engine()

        # sanity checks 
        self._sanity_check_connection(engine)
        self._sanity_check_table(engine, table)

        # preview sanity read (fast
        try:
            preview_sql = f"SELECT * FROM {table} LIMIT 5"
            preview_df = pl.read_database(preview_sql, connection=engine)
        except Exception as e:
            raise DataLoadingError(
                f"Failed to read from table '{table}'"
            ) from e

        if preview_df.width == 0:
            raise EmptyDatasetError(
                f"Table '{table}' has no columns"
            )

        if preview_df.height == 0:
            raise EmptyDatasetError(
                f"Table '{table}' contains no rows"
            )
        
        # full load
        try:
            sql = f"SELECT * FROM {table}"
            return pl.read_database(sql, connection=engine)
        except Exception as e:
            raise DataLoadingError(
                f"Failed to fully load table '{table}'"
            ) from e