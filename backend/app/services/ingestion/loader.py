import io
import re
from typing import Tuple, List, Dict, Any
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.exceptions import IngestionError
from backend.app.core.logging import logger
from backend.app.models.dataset import ColumnSchema


class DatasetLoader:
    CSV_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]

    @staticmethod
    def sanitize_column_name(col: Any, existing_names: set, index: int) -> str:
        """
        Sanitizes column name to be a safe SQL/DuckDB identifier.
        """
        col_str = str(col).strip() if col is not None else f"column_{index}"
        if not col_str:
            col_str = f"column_{index}"

        # Replace non-alphanumeric characters with underscore
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", col_str)
        # Collapse multiple underscores
        clean_name = re.sub(r"_+", "_", clean_name).strip("_")

        # Must not start with a digit
        if clean_name and clean_name[0].isdigit():
            clean_name = f"col_{clean_name}"

        if not clean_name:
            clean_name = f"column_{index}"

        # Ensure uniqueness
        base_name = clean_name
        counter = 1
        while clean_name.lower() in existing_names:
            clean_name = f"{base_name}_{counter}"
            counter += 1

        existing_names.add(clean_name.lower())
        return clean_name

    @classmethod
    def load_csv(cls, content: bytes) -> pd.DataFrame:
        """Loads CSV bytes attempting multiple common encodings and delimiter sniffing."""
        last_err = None
        for encoding in cls.CSV_ENCODINGS:
            try:
                # First try standard comma
                df = pd.read_csv(io.BytesIO(content), encoding=encoding, engine="python", on_bad_lines="skip")
                if df.shape[1] == 1:
                    # Check if delimiter is something else (semicolon, tab, pipe)
                    for sep in [";", "\t", "|"]:
                        try:
                            alt_df = pd.read_csv(io.BytesIO(content), encoding=encoding, sep=sep, engine="python", on_bad_lines="skip")
                            if alt_df.shape[1] > 1:
                                df = alt_df
                                break
                        except Exception:
                            pass
                logger.info(f"Successfully loaded CSV with encoding={encoding}, shape={df.shape}")
                return df
            except Exception as e:
                last_err = e
                continue

        raise IngestionError(f"Failed to decode CSV with supported encodings. Error: {str(last_err)}")

    @classmethod
    def load_excel(cls, content: bytes, ext: str) -> pd.DataFrame:
        """Loads Excel (.xlsx/.xls) bytes."""
        try:
            engine = "openpyxl" if ext == ".xlsx" else None
            df = pd.read_excel(io.BytesIO(content), engine=engine)
            logger.info(f"Successfully loaded Excel with shape={df.shape}")
            return df
        except Exception as e:
            raise IngestionError(f"Failed to parse Excel spreadsheet: {str(e)}")

    @classmethod
    def load_and_sanitize(cls, content: bytes, extension: str) -> Tuple[pd.DataFrame, List[ColumnSchema]]:
        """
        Loads dataset bytes into a sanitized pandas DataFrame with ColumnSchema metadata.
        """
        ext = extension.lower()
        if ext == ".csv":
            df = cls.load_csv(content)
        elif ext in [".xlsx", ".xls"]:
            df = cls.load_excel(content, ext)
        else:
            raise IngestionError(f"Unsupported file extension: {ext}")

        if df.empty or df.shape[0] == 0:
            raise IngestionError("Dataset contains no rows of data.")

        if df.shape[1] == 0:
            raise IngestionError("Dataset contains no columns.")

        if df.shape[0] > settings.MAX_DATASET_ROWS:
            raise IngestionError(
                f"Dataset row count ({df.shape[0]:,}) exceeds maximum limit of {settings.MAX_DATASET_ROWS:,} rows."
            )

        if df.shape[1] > settings.MAX_DATASET_COLUMNS:
            raise IngestionError(
                f"Dataset column count ({df.shape[1]}) exceeds maximum limit of {settings.MAX_DATASET_COLUMNS} columns."
            )

        # Sanitize column names
        original_columns = list(df.columns)
        used_names = set()
        sanitized_columns = []
        column_schemas = []

        for idx, col in enumerate(original_columns):
            clean_name = cls.sanitize_column_name(col, used_names, idx)
            sanitized_columns.append(clean_name)

            series = df.iloc[:, idx]
            null_count = int(series.isna().sum())
            non_null_samples = series.dropna().head(3).tolist()
            # Convert non-serializable objects to string representation
            clean_samples = [str(x) if not isinstance(x, (int, float, bool, str)) else x for x in non_null_samples]

            column_schemas.append(
                ColumnSchema(
                    name=clean_name,
                    original_name=str(col),
                    dtype=str(series.dtype),
                    null_count=null_count,
                    sample_values=clean_samples
                )
            )

        df.columns = sanitized_columns
        return df, column_schemas
