import asyncio
import json
import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.core.logging import logger
from backend.app.orchestration.graph import analysis_workflow_graph
from backend.app.orchestration.events import STEP_METADATA, TOTAL_PIPELINE_STEPS, format_sse_event

router = APIRouter(prefix="/api/analyze", tags=["Multi-Agent Pipeline & SSE"])


async def event_generator_from_graph(initial_state: dict) -> AsyncGenerator[str, None]:
    """Asynchronously iterates through LangGraph nodes and streams SSE events to the client."""
    dataset_id = initial_state.get("dataset_id") or str(uuid.uuid4())
    logger.info(f"Starting SSE analysis pipeline stream for dataset '{dataset_id}'")

    yield format_sse_event("pipeline_start", {
        "dataset_id": dataset_id,
        "filename": initial_state.get("filename", "dataset.csv"),
        "total_steps": TOTAL_PIPELINE_STEPS,
        "status": "initializing"
    })

    current_state = initial_state.copy()
    current_state["dataset_id"] = dataset_id

    try:
        # Stream events node by node
        async for event in analysis_workflow_graph.astream(current_state):
            for node_name, node_output in event.items():
                meta = STEP_METADATA.get(node_name, {"index": 0, "label": node_name, "agent": "Agent"})
                idx = meta["index"]
                label = meta["label"]
                agent = meta["agent"]

                # Extract partial preview data for frontend live cards
                preview_snippet = None
                if node_name == "profile_and_audit" and "quality" in node_output:
                    q = node_output["quality"]
                    preview_snippet = {"quality_score": q.quality_score, "grade": q.grade}
                elif node_name == "understand_dataset" and "understanding" in node_output:
                    u = node_output["understanding"]
                    preview_snippet = {"domain": u.domain, "kpis": [k.name for k in u.key_kpis[:3]]}
                elif node_name == "run_statistical_analysis" and "statistics" in node_output:
                    s = node_output["statistics"]
                    preview_snippet = {"metrics_count": len(s.univariate_metrics), "correlations_count": len(s.correlation_results)}
                elif node_name == "generate_insights" and "insights" in node_output:
                    ins = node_output["insights"]
                    preview_snippet = {"insights_count": len(ins.insights), "top_title": ins.insights[0].title if ins.insights else None}
                elif node_name == "generate_report" and "report" in node_output:
                    r = node_output["report"]
                    preview_snippet = {"report_title": r.title, "sections_count": len(r.sections)}

                # Emit step progress event
                yield format_sse_event("step_complete", {
                    "step": node_name,
                    "step_index": idx,
                    "total_steps": TOTAL_PIPELINE_STEPS,
                    "label": label,
                    "agent": agent,
                    "preview": preview_snippet,
                    "status": "completed"
                })

                # Update current state with output
                current_state.update(node_output)
                await asyncio.sleep(0.05)  # Yield execution smoothly

        # Pipeline completed
        final_report = current_state.get("report")
        report_dict = final_report.model_dump(mode="json") if final_report else None
        yield format_sse_event("complete", {
            "dataset_id": dataset_id,
            "filename": initial_state.get("filename", "dataset.csv"),
            "report": report_dict,
            "status": "success"
        })
        logger.info(f"SSE analysis pipeline stream finished successfully for '{dataset_id}'")

    except asyncio.CancelledError:
        logger.info(f"Pipeline streaming cancelled by client for '{dataset_id}'")
        return
    except Exception as e:
        logger.exception(f"Pipeline streaming error for '{dataset_id}': {str(e)}")
        yield format_sse_event("error", {
            "dataset_id": dataset_id,
            "error": str(e),
            "step": current_state.get("current_step", "unknown")
        })


@router.post("/stream")
async def analyze_file_stream(
    file: UploadFile = File(...)
):
    """
    Accepts CSV/Excel upload and streams real-time execution progress of the
    17-node LangGraph multi-agent pipeline via Server-Sent Events (SSE).
    """
    logger.info(f"Received file upload for SSE pipeline: {file.filename}")
    try:
        content = await file.read()
        dataset_id = str(uuid.uuid4())

        initial_state: dict = {
            "dataset_id": dataset_id,
            "filename": file.filename or "dataset.csv",
            "file_bytes": content,
            "logs": [],
            "revision_count": 0,
            "critic_approved": False
        }

        return StreamingResponse(
            event_generator_from_graph(initial_state),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Failed to initiate stream: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
