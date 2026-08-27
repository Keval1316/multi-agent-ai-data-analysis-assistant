import os
import re
from typing import Tuple
from backend.app.core.config import settings
from backend.app.core.exceptions import FileValidationError

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "text/plain",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",  # Fallback for some OS/browser uploads
}


class FileValidator:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizes raw uploaded filename to prevent directory traversal and special character injection."""
        if not filename:
            raise FileValidationError("Filename cannot be empty")
        
        # Remove any path components
        base = os.path.basename(filename)
        # Keep only alphanumeric, dots, underscores, hyphens
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
        if not sanitized or sanitized.startswith("."):
            sanitized = f"upload_{sanitized}".lstrip(".")
        return sanitized

    @staticmethod
    def validate_file_metadata(filename: str, file_size: int, content_type: str = "") -> Tuple[str, str]:
        """
        Validates basic file metadata before heavy processing.
        Returns (sanitized_filename, extension).
        """
        if not filename:
            raise FileValidationError("No filename provided")

        sanitized_name = FileValidator.sanitize_filename(filename)
        _, ext = os.path.splitext(sanitized_name.lower())

        if ext not in ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        if file_size <= 0:
            raise FileValidationError("The uploaded file is empty (0 bytes).")

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise FileValidationError(
                f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        return sanitized_name, ext
