import os
import pytest
from backend.app.orchestration.graph import analysis_workflow_graph


@pytest.fixture
def clean_file_bytes():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        return f.read()


def test_full_17_node_langgraph_execution(clean_file_bytes):
    initial_state = {
        "dataset_id": "test_graph_ds",
        "filename": "clean_dataset.csv",
        "file_bytes": clean_file_bytes,
        "logs": [],
        "revision_count": 0,
        "critic_approved": False
    }

    final_state = analysis_workflow_graph.invoke(initial_state)

    # 1. Check core state artifacts
    assert final_state["dataset_id"] == "test_graph_ds"
    assert final_state["table_name"] == "dataset_test_graph_ds"
    assert final_state["profile"] is not None
    assert final_state["quality"] is not None
    assert final_state["understanding"] is not None
    assert final_state["plan"] is not None
    assert final_state["statistics"] is not None
    assert len(final_state["sql_queries"]) > 0
    assert final_state["sql_results"] is not None
    assert final_state["patterns"] is not None
    assert final_state["charts"] is not None
    assert final_state["insights"] is not None
    assert final_state["critic_review"] is not None
    assert final_state["report"] is not None
    assert final_state["pdf_bytes"] is not None
    assert len(final_state["pdf_bytes"]) > 1000

    # 2. Check final report structure
    report = final_state["report"]
    assert report.title != ""
    assert len(report.sections) >= 3
    assert len(report.insights.insights) >= 1
