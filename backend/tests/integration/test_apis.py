import os
import asyncio
import litellm
import yaml
import sys
from dotenv import load_dotenv

# Silence litellm verbose logging for clean test output
os.environ["LITELLM_LOG"] = "ERROR"

load_dotenv()

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm.key_manager import KeyManager

async def test_all():
    # Load fallback config to get a valid model for each provider
    try:
        with open("litellm_fallback_config.yaml") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    # Collect one model per provider from config
    provider_models = {}
    for tier in ["tier1", "tier2", "tier3", "tier4"]:
        for entry in config.get("fallback_chain", {}).get(tier, []):
            provider = entry["provider"]
            if provider not in provider_models:
                provider_models[provider] = entry["model"]

    km = KeyManager()
    providers = km.get_available_providers()
    print(f"Discovered Providers with keys: {providers}")
    
    for provider in providers:
        print(f"\n--- Testing Provider: {provider.upper()} ---")
        model = provider_models.get(provider)
        if not model:
            print(f"Skipping {provider} - no model configured in litellm_fallback_config.yaml.")
            continue
            
        print(f"Using mapped model: {model}")
        keys_count = km.get_key_count(provider)
        print(f"Found {keys_count} configured key(s).")
        
        for i in range(keys_count):
            api_key = km.get_active_key(provider)
            account_id = km.get_active_account_id(provider, api_key)
            kwargs = {}
            if account_id:
                kwargs["cloudflare_account_id"] = account_id
                
            key_preview = api_key[:10] + "..." if api_key else "None"
            print(f"  Testing Key {i+1}/{keys_count} ({key_preview}): ", end="", flush=True)
            
            try:
                response = await litellm.acompletion(
                    model=model,
                    messages=[{"role": "user", "content": "Reply with exactly 'OK'"}],
                    api_key=api_key,
                    max_tokens=10,
                    **kwargs
                )
                print("SUCCESS (" + response.choices[0].message.content.strip() + ")")
            except Exception as e:
                # Get the core error message
                err_msg = str(e).split("\n")[0]
                print(f"FAILED - {err_msg}")

if __name__ == "__main__":
    asyncio.run(test_all())
