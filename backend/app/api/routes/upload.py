import os
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import FileValidationError, IngestionError
from backend.app.models.dataset import DatasetMetadata, UploadResponse
from backend.app.services.ingestion.validator import FileValidator
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager

router = APIRouter(prefix="/api", tags=["Ingestion"])

TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "temp_uploads")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Validates, parses, and ingests a CSV or Excel dataset into DuckDB.
    Returns dataset metadata, inferred schema, and preview rows.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    logger.info(f"Received upload request for file: '{file.filename}', content_type: '{file.content_type}'")

    try:
        # Read file contents into memory
        content = await file.read()
        file_size = len(content)

        # 1. Validate file metadata
        sanitized_name, extension = FileValidator.validate_file_metadata(
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type or ""
        )

        # 2. Parse & sanitize DataFrame
        df, column_schemas = DatasetLoader.load_and_sanitize(content, extension)

        # 3. Register in DuckDB
        dataset_id, table_name = duckdb_manager.register_dataframe(df)

        # 4. Save temporary file safely
        safe_file_path = os.path.join(TEMP_UPLOAD_DIR, f"{dataset_id}_{sanitized_name}")
        with open(safe_file_path, "wb") as f:
            f.write(content)

        # 5. Fetch preview rows
        preview_rows = duckdb_manager.get_preview_rows(table_name, limit=5)

        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            table_name=table_name,
            filename=sanitized_name,
            file_size_bytes=file_size,
            row_count=int(df.shape[0]),
            column_count=int(df.shape[1]),
            columns=column_schemas,
            preview_rows=preview_rows,
            upload_timestamp=datetime.now(timezone.utc).isoformat()
        )

        logger.info(f"Successfully ingested dataset '{sanitized_name}' (ID: {dataset_id}, Rows: {df.shape[0]}, Cols: {df.shape[1]})")

        return UploadResponse(
            success=True,
            message="Dataset uploaded, parsed, and registered successfully.",
            dataset=metadata
        )

    except FileValidationError as e:
        logger.warning(f"File validation failed for '{file.filename}': {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except IngestionError as e:
        logger.warning(f"Ingestion failed for '{file.filename}': {e.message}")
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.exception(f"Unexpected error during upload of '{file.filename}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error while ingesting dataset.")
