import os
import pytest
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.patterns.detector import PatternDetector


@pytest.fixture
def clean_dataset():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    profile = DatasetProfiler.profile_dataset(df, "clean_ds", "dataset_clean_ds")
    return df, profile


@pytest.fixture
def messy_dataset():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "messy_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    profile = DatasetProfiler.profile_dataset(df, "messy_ds", "dataset_messy_ds")
    return df, profile


def test_pattern_detection_clean_dataset(clean_dataset):
    df, profile = clean_dataset
    result = PatternDetector.detect_all(df, profile)

    assert result.dataset_id == "clean_ds"
    assert len(result.trends) > 0
    assert len(result.concentrations) > 0
    assert len(result.key_findings) > 0

    # Trend check
    trend = result.trends[0]
    assert trend.direction in ["increasing", "decreasing", "stable"]
    assert trend.metric_column in profile.numeric_column_names

    # Pareto concentration check
    conc = result.concentrations[0]
    assert conc.top_categories_share_pct > 0
    assert len(conc.top_category_names) > 0


def test_anomaly_detection_messy_dataset(messy_dataset):
    df, profile = messy_dataset
    result = PatternDetector.detect_all(df, profile)

    # In messy_dataset, quantity has 99999 and total_revenue has 44,999,550
    assert len(result.anomalies) > 0
    extreme_anomaly = next((a for a in result.anomalies if a.severity == "high"), None)
    assert extreme_anomaly is not None
    assert abs(extreme_anomaly.z_score) >= 3.0
