from typing import Dict
from fastapi import APIRouter, HTTPException
from backend.app.core.logging import logger
from backend.app.models.profile import DatasetProfile
from backend.app.models.quality import QualityReport
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.quality.checker import QualityChecker

router = APIRouter(prefix="/api/dataset", tags=["Profiling & Quality"])

# In-memory caches for fast retrieval
_profile_cache: Dict[str, DatasetProfile] = {}
_quality_cache: Dict[str, QualityReport] = {}


def get_or_create_profile(dataset_id: str) -> DatasetProfile:
    if dataset_id in _profile_cache:
        return _profile_cache[dataset_id]

    table_name = duckdb_manager.registered_tables.get(dataset_id) or duckdb_manager.generate_table_name(dataset_id)
    if not duckdb_manager.table_exists(table_name):
        raise HTTPException(status_code=404, detail=f"Dataset with ID '{dataset_id}' not found in database.")

    try:
        df = duckdb_manager.execute_query(f"SELECT * FROM {table_name}")
        profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)
        _profile_cache[dataset_id] = profile
        return profile
    except Exception as e:
        logger.exception(f"Failed to profile dataset '{dataset_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profiling failed: {str(e)}")


@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
async def get_dataset_profile(dataset_id: str):
    """Computes and returns deterministic column distributions, null summaries, and statistics."""
    logger.info(f"Fetching profile for dataset '{dataset_id}'")
    return get_or_create_profile(dataset_id)


@router.get("/{dataset_id}/quality", response_model=QualityReport)
async def get_dataset_quality(dataset_id: str):
    """Audits data quality, classifies issues (confirmed, suspicious, informational), and computes a 0-100 quality score."""
    logger.info(f"Auditing data quality for dataset '{dataset_id}'")
    if dataset_id in _quality_cache:
        return _quality_cache[dataset_id]

    profile = get_or_create_profile(dataset_id)
    table_name = profile.table_name

    try:
        df = duckdb_manager.execute_query(f"SELECT * FROM {table_name}")
        report = QualityChecker.audit_dataset(df, profile)
        _quality_cache[dataset_id] = report
        return report
    except Exception as e:
        logger.exception(f"Failed to audit dataset quality '{dataset_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quality audit failed: {str(e)}")
