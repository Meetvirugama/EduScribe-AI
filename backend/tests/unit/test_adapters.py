import pytest
from unittest.mock import MagicMock, patch
from services.llm.providers.adapters import (
    ProviderAdapterFactory,
    DefaultAdapter,
    CloudflareAdapter
)

@pytest.fixture
def mock_key_manager():
    return MagicMock()

def test_default_adapter(mock_key_manager):
    adapter = DefaultAdapter(mock_key_manager)
    kwargs = adapter.prepare_request("openai", "gpt-4o", "sk-123")
    
    assert kwargs == {}

def test_cloudflare_adapter_with_account_id(mock_key_manager):
    mock_key_manager.get_active_account_id.return_value = "acc-12345"
    adapter = CloudflareAdapter(mock_key_manager)
    
    kwargs = adapter.prepare_request("cloudflare", "@cf/meta/llama-2-7b-chat-int8", "sk-123")
    
    assert "api_base" in kwargs
    assert kwargs["api_base"] == "https://api.cloudflare.com/client/v4/accounts/acc-12345/ai/run/"
    mock_key_manager.get_active_account_id.assert_called_once_with("cloudflare", "sk-123")

@patch("services.llm.providers.adapters.logger.warning")
def test_cloudflare_adapter_without_account_id(mock_warning, mock_key_manager):
    mock_key_manager.get_active_account_id.return_value = None
    adapter = CloudflareAdapter(mock_key_manager)
    
    kwargs = adapter.prepare_request("cloudflare", "@cf/meta/llama-2-7b-chat-int8", "sk-123")
    
    assert kwargs == {}
    mock_warning.assert_called_once()
    assert "No account_id found" in mock_warning.call_args[0][0]

def test_provider_adapter_factory(mock_key_manager):
    factory = ProviderAdapterFactory(mock_key_manager)
    
    # 1. Exact match
    adapter_cf = factory.get_adapter("cloudflare")
    assert isinstance(adapter_cf, CloudflareAdapter)
    
    # 2. Case and whitespace normalization
    adapter_cf2 = factory.get_adapter("  CloudFlare  ")
    assert isinstance(adapter_cf2, CloudflareAdapter)
    
    # 3. Unknown provider routing to DefaultAdapter
    adapter_openai = factory.get_adapter("openai")
    assert isinstance(adapter_openai, DefaultAdapter)
    
    # 4. None routing to DefaultAdapter safely
    adapter_none = factory.get_adapter(None)
    assert isinstance(adapter_none, DefaultAdapter)
