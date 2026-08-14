import pytest
from unittest.mock import patch, MagicMock
from services.llm.quota_tracker import QuotaTracker, PROVIDER_QUOTA_POLICIES, QuotaPolicy

@pytest.fixture
def quota_tracker():
    # Use in-memory tracker
    return QuotaTracker(redis_url="invalid_url_to_force_in_memory")

def test_has_quota_request_token(quota_tracker):
    # groq uses request_token
    # default rpd is 14400
    assert quota_tracker.has_quota("groq") is True
    quota_tracker._in_memory["groq"] = {"rpd": 14400, "tokens": 0}
    assert quota_tracker.has_quota("groq") is False

    # llama-3.3-70b-versatile has a limit of 1000
    quota_tracker._in_memory["groq"] = {"rpd": 999, "tokens": 0}
    assert quota_tracker.has_quota("groq", "llama-3.3-70b-versatile") is True
    quota_tracker._in_memory["groq"] = {"rpd": 1000, "tokens": 0}
    assert quota_tracker.has_quota("groq", "llama-3.3-70b-versatile") is False

def test_has_quota_compute_credit(quota_tracker):
    # cloudflare uses compute_credit, which doesn't block pre-flight right now
    quota_tracker._in_memory["cloudflare"] = {"rpd": 100000, "tokens": 1000000}
    assert quota_tracker.has_quota("cloudflare") is True

def test_has_quota_one_time_balance(quota_tracker):
    # jina uses one_time_balance (10,000,000 tokens)
    assert quota_tracker.has_quota("jina") is True
    quota_tracker._in_memory["jina"] = {"rpd": 0, "tokens": 10000000}
    assert quota_tracker.has_quota("jina") is False

def test_has_quota_monthly_call_cap(quota_tracker):
    # cohere uses monthly_call_cap (1000 calls)
    assert quota_tracker.has_quota("cohere") is True
    quota_tracker._in_memory["cohere"] = {"rpd": 1000, "tokens": 0}
    assert quota_tracker.has_quota("cohere") is False

def test_has_quota_flat_daily_cap(quota_tracker):
    # openrouter uses flat_daily_cap (50)
    assert quota_tracker.has_quota("openrouter") is True
    quota_tracker._in_memory["openrouter"] = {"rpd": 50, "tokens": 0}
    assert quota_tracker.has_quota("openrouter") is False

def test_record_request(quota_tracker):
    assert quota_tracker._get_rpd_used("groq") == 0
    assert quota_tracker._get_tokens_used("groq") == 0

    quota_tracker.record_request("groq", "llama-3.1-8b-instant", tokens_used=150)
    assert quota_tracker._get_rpd_used("groq") == 1
    assert quota_tracker._get_tokens_used("groq") == 150
