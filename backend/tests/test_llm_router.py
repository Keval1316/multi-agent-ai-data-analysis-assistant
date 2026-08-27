import time
import pytest
from backend.app.llm.privacy import DataPrivacyFilter
from backend.app.llm.mock_provider import MockLLMProvider
from backend.app.llm.router import LLMRouter
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.models.plan import AnalysisPlan


def test_privacy_filter_redaction():
    text = (
        "User contact is john.doe@example.com or support@company.org. "
        "Phone number is 555-123-4567, SSN is 123-45-6789, "
        "and api_key=sk-1234567890abcdef."
    )
    redacted = DataPrivacyFilter.redact_text(text)
    assert "john.doe@example.com" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert "555-123-4567" not in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "123-45-6789" not in redacted
    assert "[SSN_REDACTED]" in redacted
    assert "sk-1234567890abcdef" not in redacted
    assert "[SECRET_REDACTED]" in redacted


def test_mock_llm_provider_understanding():
    mock = MockLLMProvider()
    messages = [{"role": "user", "content": "Columns: 'revenue', 'quantity', 'region', 'category'"}]
    res = mock.generate_structured(messages, DatasetUnderstanding)

    assert isinstance(res, DatasetUnderstanding)
    assert res.domain != ""
    assert len(res.key_kpis) >= 1
    assert len(res.core_questions) >= 2


def test_mock_llm_provider_plan():
    mock = MockLLMProvider()
    messages = [{"role": "user", "content": "Columns: 'total_revenue', 'quantity', 'region', 'category'"}]
    res = mock.generate_structured(messages, AnalysisPlan)

    assert isinstance(res, AnalysisPlan)
    assert res.primary_goal != ""
    assert len(res.sql_query_goals) >= 1
    assert len(res.recommended_charts) >= 1


def test_router_cooldown_and_fallback():
    router = LLMRouter.get_instance()

    # Place a fake key on cooldown
    router.mark_cooldown("test_key_1")
    assert router.is_cooling_down("test_key_1") is True

    # Complete using router (falls back gracefully to MockLLMProvider when no keys configured)
    messages = [{"role": "user", "content": "Columns: 'sales', 'profit', 'region'"}]
    res = router.complete(
        agent_name="test_agent",
        messages=messages,
        response_model=DatasetUnderstanding
    )
    assert isinstance(res, DatasetUnderstanding)
    assert len(res.key_kpis) >= 1
