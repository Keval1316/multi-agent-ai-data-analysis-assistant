import re
from typing import Tuple, Set, Optional
from backend.app.core.exceptions import SQLSecurityError
from backend.app.core.logging import logger


class SQLValidator:
    """Strict SQL security validator permitting only safe, read-only analytical DuckDB queries."""

    # Disallowed mutating or environment-escaping SQL keywords
    DISALLOWED_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE",
        "COPY", "ATTACH", "DETACH", "INSTALL", "LOAD", "PRAGMA", "IMPORT",
        "EXPORT", "EXEC", "EXECUTE", "SYSTEM", "CALL", "GRANT", "REVOKE",
        "TRUNCATE", "VACUUM", "CHECKPOINT", "REINDEX"
    }

    # Disallowed external file/network scanning functions
    DISALLOWED_FUNCTIONS = {
        "read_csv", "read_parquet", "scan_parquet", "read_json", "read_blob",
        "httpfs", "parquet_scan", "glob", "write_csv", "write_parquet"
    }

    @classmethod
    def validate_sql(
        cls,
        sql: str,
        expected_table: Optional[str] = None,
        valid_columns: Optional[Set[str]] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        Validates SQL safety.
        Returns (is_safe: bool, rejection_reason: Optional[str], sanitized_sql: str).
        """
        if not sql or not sql.strip():
            return False, "SQL query cannot be empty", ""

        cleaned = sql.strip()

        # 1. Multi-statement injection check (semicolon inside query)
        # Strip trailing semicolon if present
        if cleaned.endswith(";"):
            cleaned = cleaned[:-1].strip()

        if ";" in cleaned:
            return False, "Multiple SQL statements separated by ';' are strictly forbidden", ""

        # 2. Must start with SELECT or WITH
        norm_sql = re.sub(r"\s+", " ", cleaned).strip()
        first_token = norm_sql.split(" ")[0].upper()
        if first_token not in ["SELECT", "WITH"]:
            return False, f"SQL statement must start with SELECT or WITH (got '{first_token}')", ""

        # 3. Disallowed Keywords Check (Word boundary match)
        for kw in cls.DISALLOWED_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", cleaned, re.IGNORECASE):
                # Verify it's not part of an identifier or alias string
                return False, f"Forbidden SQL keyword detected: '{kw}'", ""

        # 4. Disallowed Functions / External Access Check
        for fn in cls.DISALLOWED_FUNCTIONS:
            if re.search(r"\b" + re.escape(fn) + r"\b", cleaned, re.IGNORECASE):
                return False, f"Forbidden external function or file access detected: '{fn}'", ""

        # 5. Check URL schemes (network access)
        if re.search(r"(https?://|s3://|gcs://|file://)", cleaned, re.IGNORECASE):
            return False, "External URL or storage protocol detected in query", ""

        # 6. Table reference verification (if expected_table provided)
        if expected_table:
            # Check if expected table is mentioned in the query
            if not re.search(r"\b" + re.escape(expected_table) + r"\b", cleaned, re.IGNORECASE):
                # If query uses a generic name like 'dataset', replace it safely with the actual table name
                if re.search(r"\bFROM\s+dataset\b", cleaned, re.IGNORECASE):
                    cleaned = re.sub(r"\bFROM\s+dataset\b", f"FROM {expected_table}", cleaned, flags=re.IGNORECASE)
                elif re.search(r"\bFROM\s+data\b", cleaned, re.IGNORECASE):
                    cleaned = re.sub(r"\bFROM\s+data\b", f"FROM {expected_table}", cleaned, flags=re.IGNORECASE)
                elif "from" in cleaned.lower():
                    pass  # Could be CTE subquery

        return True, None, cleaned
