import pandas as pd
from fastapi import APIRouter, HTTPException, Response
from backend.app.core.logging import logger
from backend.app.models.report import AnalysisReport
from backend.app.services.reporting.report_builder import ReportBuilder
from backend.app.services.reporting.pdf_exporter import PDFExporter
from backend.app.services.ingestion.duckdb_manager import duckdb_manager

router = APIRouter(prefix="/api/dataset", tags=["Reporting & PDF Export"])


@router.get("/history")
async def get_analysis_history():
    """Retrieves list of past analyzed datasets and reports from session history."""
    logger.info("Received request for analysis history")
    return {"history": ReportBuilder.list_history()}


@router.delete("/{dataset_id}")
async def delete_analysis_record(dataset_id: str):
    """Deletes an analysis report and cleans up resources for a dataset."""
    logger.info(f"Received request to delete analysis for '{dataset_id}'")
    deleted = ReportBuilder.delete_report(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found in active session.")
    return {"success": True, "message": f"Dataset '{dataset_id}' deleted successfully."}


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


@router.post("/report/pdf")
@router.post("/{dataset_id}/report/pdf")
async def generate_pdf_from_payload(report: AnalysisReport, dataset_id: str = ""):
    """Generates and streams a publication-ready PDF directly from an AnalysisReport JSON payload."""
    target_id = report.dataset_id or dataset_id or "export"
    logger.info(f"Received direct POST request for PDF generation on dataset '{target_id}'")
    try:
        ReportBuilder.cache_report(report)
        pdf_bytes = PDFExporter.generate_pdf(report)
        filename = f"analysis_report_{target_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes))
            }
        )
    except Exception as e:
        logger.error(f"Error rendering PDF from payload for '{target_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to render PDF: {str(e)}")


@router.get("/{dataset_id}/report/pdf")
async def download_pdf_report(dataset_id: str):
    """Generates and streams a publication-ready PDF download for the dataset report."""
    logger.info(f"Received request for PDF download on dataset '{dataset_id}'")

    # 1. Fetch or build report
    report = ReportBuilder.get_report(dataset_id)
    if not report:
        tbl = duckdb_manager.generate_table_name(dataset_id)
        if duckdb_manager.table_exists(tbl):
            df = duckdb_manager.get_dataframe(tbl)
            report = ReportBuilder.build_report_from_dataset(df, dataset_id, tbl, f"{dataset_id}.csv")
        else:
            cleaned_df = ReportBuilder.get_cleaned_df(dataset_id)
            if cleaned_df is not None:
                report = ReportBuilder.build_report_from_dataset(cleaned_df, dataset_id, tbl, f"{dataset_id}.csv")

    if not report:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

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


@router.get("/{dataset_id}/download/cleaned-csv")
async def download_cleaned_csv(dataset_id: str):
    """Generates and streams the sanitized, production-ready CSV dataset."""
    logger.info(f"Received request for cleaned CSV download on dataset '{dataset_id}'")
    from backend.app.services.cleaning.cleaner import DataCleaner

    cleaned_df = ReportBuilder.get_cleaned_df(dataset_id)
    report = ReportBuilder.get_report(dataset_id)
    filename = report.filename if report else f"{dataset_id}.csv"
    clean_base = filename.rsplit(".", 1)[0] if "." in filename else filename

    if cleaned_df is None:
        tbl = duckdb_manager.generate_table_name(dataset_id)
        if not duckdb_manager.table_exists(tbl):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
        df = duckdb_manager.get_dataframe(tbl)
        cleaned_df, cleaning_summary = DataCleaner.clean_dataset(df, dataset_id, filename)
        ReportBuilder.cache_cleaned_df(dataset_id, cleaned_df)

    try:
        csv_bytes = DataCleaner.export_csv_bytes(cleaned_df)
        download_filename = f"cleaned_{clean_base}.csv"
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes))
            }
        )
    except Exception as e:
        logger.error(f"Error exporting cleaned CSV for '{dataset_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export cleaned CSV: {str(e)}")


@router.get("/{dataset_id}/download/cleaned-excel")
async def download_cleaned_excel(dataset_id: str):
    """Generates and streams the sanitized, styled Excel (.xlsx) dataset."""
    logger.info(f"Received request for cleaned Excel download on dataset '{dataset_id}'")
    from backend.app.services.cleaning.cleaner import DataCleaner

    cleaned_df = ReportBuilder.get_cleaned_df(dataset_id)
    report = ReportBuilder.get_report(dataset_id)
    filename = report.filename if report else f"{dataset_id}.csv"
    clean_base = filename.rsplit(".", 1)[0] if "." in filename else filename

    if cleaned_df is None:
        tbl = duckdb_manager.generate_table_name(dataset_id)
        if not duckdb_manager.table_exists(tbl):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
        df = duckdb_manager.get_dataframe(tbl)
        cleaned_df, _ = DataCleaner.clean_dataset(df, dataset_id, filename)
        ReportBuilder.cache_cleaned_df(dataset_id, cleaned_df)

    try:
        excel_bytes = DataCleaner.export_excel_bytes(cleaned_df, sheet_name="Cleaned Data")
        download_filename = f"cleaned_{clean_base}.xlsx"
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(excel_bytes))
            }
        )
    except Exception as e:
        logger.error(f"Error exporting cleaned Excel for '{dataset_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export cleaned Excel: {str(e)}")


@router.get("/{dataset_id}/cleaned-preview")
async def get_cleaned_preview(dataset_id: str):
    """Returns top 20 rows and transformation summary of the cleaned dataset for UI preview."""
    logger.info(f"Received request for cleaned preview on dataset '{dataset_id}'")
    from backend.app.services.cleaning.cleaner import DataCleaner

    cleaned_df = ReportBuilder.get_cleaned_df(dataset_id)
    report = ReportBuilder.get_report(dataset_id)

    if cleaned_df is None:
        tbl = duckdb_manager.generate_table_name(dataset_id)
        if not duckdb_manager.table_exists(tbl):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
        df = duckdb_manager.get_dataframe(tbl)
        filename = report.filename if report else "dataset.csv"
        cleaned_df, cleaning_summary = DataCleaner.clean_dataset(df, dataset_id, filename)
        ReportBuilder.cache_cleaned_df(dataset_id, cleaned_df)
        if report:
            report.cleaning_summary = cleaning_summary.model_dump()

    # Replace NaNs/Infs for JSON serialization
    clean_preview = cleaned_df.head(20).where(pd.notnull(cleaned_df.head(20)), None)
    return {
        "dataset_id": dataset_id,
        "total_rows": len(cleaned_df),
        "total_columns": len(cleaned_df.columns),
        "columns": list(cleaned_df.columns),
        "rows": clean_preview.to_dict(orient="records"),
        "cleaning_summary": report.cleaning_summary if report else None
    }
