import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
import duckdb
import pandas as pd
from backend.app.core.exceptions import IngestionError
from backend.app.core.logging import logger


class DuckDBManager:
    """Manages DuckDB in-memory database connections and dataset table registrations."""
    _instance: Optional["DuckDBManager"] = None

    def __init__(self):
        self.conn = duckdb.connect(database=":memory:", read_only=False)
        self.registered_tables: Dict[str, str] = {}  # dataset_id -> table_name

    @classmethod
    def get_instance(cls) -> "DuckDBManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def generate_table_name(dataset_id: str) -> str:
        """Generates a clean DuckDB table name from dataset ID."""
        clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", dataset_id)
        return f"dataset_{clean_id}"

    def register_dataframe(self, df: pd.DataFrame, dataset_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Registers a pandas DataFrame into DuckDB.
        Returns (dataset_id, table_name).
        """
        try:
            if not dataset_id:
                dataset_id = str(uuid.uuid4())

            table_name = self.generate_table_name(dataset_id)
            
            # Register in DuckDB
            # DuckDB allows creating table directly from DataFrame
            self.conn.register("temp_df_view", df)
            self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM temp_df_view")
            self.conn.unregister("temp_df_view")

            self.registered_tables[dataset_id] = table_name
            logger.info(f"Registered table '{table_name}' in DuckDB for dataset '{dataset_id}' with {len(df)} rows")
            return dataset_id, table_name
        except Exception as e:
            logger.exception(f"Failed to register DataFrame in DuckDB: {str(e)}")
            raise IngestionError(f"Failed to register dataset in DuckDB: {str(e)}")

    def get_preview_rows(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetches top preview rows as a list of dicts with JSON-safe types."""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result_df = self.conn.execute(query).df()
            # Replace NaNs/Infs with None for clean JSON serialization
            clean_df = result_df.where(pd.notnull(result_df), None)
            return clean_df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Failed to fetch preview rows for table '{table_name}': {str(e)}")
            return []

    def get_dataframe(self, table_name: str) -> pd.DataFrame:
        """Retrieves an entire table as a pandas DataFrame."""
        return self.conn.execute(f"SELECT * FROM {table_name}").df()

    def execute_query(self, query: str) -> pd.DataFrame:
        """Executes a SQL query against the DuckDB instance and returns a pandas DataFrame."""
        return self.conn.execute(query).df()

    def drop_table(self, table_name: str):
        """Drops a table if it exists in DuckDB."""
        try:
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            for k, v in list(self.registered_tables.items()):
                if v == table_name:
                    del self.registered_tables[k]
            logger.info(f"Dropped DuckDB table '{table_name}'")
        except Exception as e:
            logger.warning(f"Error dropping table '{table_name}': {e}")

    def table_exists(self, table_name: str) -> bool:
        """Checks if a table exists in DuckDB."""
        try:
            result = self.conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table_name]
            ).fetchone()
            return bool(result and result[0] > 0)
        except Exception:
            return False


duckdb_manager = DuckDBManager.get_instance()
