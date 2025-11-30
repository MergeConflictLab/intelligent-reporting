import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Engine
import polars as pl

class DBLoader:
    def __init__(self, *, db_url: str = None, engine: Engine = None):
        """
        Only one of db_url or engine should be provided
        """
        if db_url and engine:
            raise ValueError("Provide only one of (db_url, engine)")
        
        if not db_url and not engine:
            raise ValueError("Please provide at least one of (db_url, engine)")

        self.db_url = db_url
        self.engine = engine

    def _get_engine(self) -> Engine:
        """
        returns an SQLAlchemy engine
        if engine was not provided, create one from db_url
        """
        if self.engine is not None:
            return self.engine

        if self.db_url is None:
            raise ValueError("No database connection available (db_url or engine)")

        # turn url connection into engine
        self.engine = sqlalchemy.create_engine(self.db_url)
        return self.engine

    def load(self, *, table: str = None) -> Engine:
        """
        Load data from the database connection set in the constructor
        Must supply either table or query
        """

        engine = self._get_engine()

        if table:
            # there is no read_sql_table in polars, so we fallback to SELECT *
            sql = f"SELECT * FROM {table}"
            return pl.read_database(sql, connection=engine)

        raise ValueError("Provide either 'table' or 'query' to load_from_db()")