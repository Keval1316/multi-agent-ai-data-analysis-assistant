from fastapi import APIRouter, HTTPException, Response
from backend.app.core.logging import logger
from backend.app.models.report import AnalysisReport
from backend.app.services.reporting.report_builder import ReportBuilder
from backend.app.services.reporting.pdf_exporter import PDFExporter
from backend.app.services.ingestion.duckdb_manager import duckdb_manager

router = APIRouter(prefix="/api/dataset", tags=["Reporting & PDF Export"])


@router.get("/{dataset_id}/report", response_model=AnalysisReport)
async def get_analysis_report(dataset_id: str):
    """Retrieves the complete compiled analysis report for a dataset."""
    logger.info(f"Received request for report on dataset '{dataset_id}'")

    # 1. Check cache first
    cached = ReportBuilder.get_report(dataset_id)
    if cached:
        return cached

    # 2. Check if registered in DuckDB to build on-demand
    tbl = duckdb_manager.generate_table_name(dataset_id)
    if not duckdb_manager.table_exists(tbl):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found in active session.")

    try:
        df = duckdb_manager.get_dataframe(tbl)
        report = ReportBuilder.build_report_from_dataset(df, dataset_id, tbl, f"{dataset_id}.csv")
        return report
    except Exception as e:
        logger.error(f"Error compiling report for '{dataset_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis report: {str(e)}")


@router.get("/{dataset_id}/report/pdf")
async def download_pdf_report(dataset_id: str):
    """Generates and streams a publication-ready PDF download for the dataset report."""
    logger.info(f"Received request for PDF download on dataset '{dataset_id}'")

    # 1. Fetch or build report
    report = ReportBuilder.get_report(dataset_id)
    if not report:
        tbl = duckdb_manager.generate_table_name(dataset_id)
        if not duckdb_manager.table_exists(tbl):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
        df = duckdb_manager.get_dataframe(tbl)
        report = ReportBuilder.build_report_from_dataset(df, dataset_id, tbl, f"{dataset_id}.csv")

    try:
        pdf_bytes = PDFExporter.generate_pdf(report)
        filename = f"analysis_report_{report.dataset_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes))
            }
        )
    except Exception as e:
        logger.error(f"Error rendering PDF for '{dataset_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to render PDF: {str(e)}")
