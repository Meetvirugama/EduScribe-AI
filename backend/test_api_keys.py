import os
import json
import urllib.request
import urllib.error

def load_env(filepath):
    env_vars = {}
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return env_vars
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Ignore comments and empty lines
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                env_vars[key] = val
    return env_vars

def check_api(name, key, url, headers=None, check_method="GET"):
    if headers is None:
        headers = {}
    
    # Do not set Authorization header if we pass key in URL (e.g. Gemini)
    if "Authorization" not in headers and "key=" not in url:
        headers["Authorization"] = f"Bearer {key}"
        
    req = urllib.request.Request(url, headers=headers, method=check_method)
        
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            if status == 200:
                print(f"✅ {name}: Valid key (Status 200)")
            else:
                print(f"⚠️ {name}: Returned status {status}")
    except urllib.error.HTTPError as e:
        print(f"❌ {name}: HTTP Error {e.code} - {e.reason}")
    except Exception as e:
        print(f"❌ {name}: Failed - {e}")

def main():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    print(f"Loading environment from {env_path}\n")
    env = load_env(env_path)
    
    # GROQ
    print("-" * 50)
    print("Testing GROQ Keys")
    print("-" * 50)
    groq_keys = env.get("GROQ_API_KEYS", "").split(",")
    for i, key in enumerate(groq_keys):
        key = key.strip()
        if key:
            check_api(f"Groq Key {i+1}", key, "https://api.groq.com/openai/v1/models")
            
    # GEMINI
    print("\n" + "-" * 50)
    print("Testing GEMINI Keys")
    print("-" * 50)
    gemini_keys = env.get("GEMINI_API_KEYS", "").split(",")
    for i, key in enumerate(gemini_keys):
        key = key.strip()
        if key:
            check_api(f"Gemini Key {i+1}", key, f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
            
    # OPENROUTER
    print("\n" + "-" * 50)
    print("Testing OPENROUTER Keys")
    print("-" * 50)
    or_keys = env.get("OPENROUTER_API_KEYS", "").split(",")
    for i, key in enumerate(or_keys):
        key = key.strip()
        if key:
            check_api(f"OpenRouter Key {i+1}", key, "https://openrouter.ai/api/v1/auth/key")
            
    # HUGGINGFACE
    print("\n" + "-" * 50)
    print("Testing HUGGINGFACE Keys")
    print("-" * 50)
    hf_keys = env.get("HUGGINGFACE_API_KEYS", "").split(",")
    for i, key in enumerate(hf_keys):
        key = key.strip()
        if key:
            check_api(f"HuggingFace Key {i+1}", key, "https://huggingface.co/api/whoami-v2")
            
    # JINA AI
    print("\n" + "-" * 50)
    print("Testing JINA AI Keys")
    print("-" * 50)
    jina_key = env.get("JINA_API_KEY", "").strip()
    if jina_key:
        check_api("Jina AI Key", jina_key, "https://api.jina.ai/v1/models")

    # COHERE
    print("\n" + "-" * 50)
    print("Testing COHERE Keys")
    print("-" * 50)
    cohere_keys = env.get("COHERE_API_KEYS", "").split(",")
    for i, key in enumerate(cohere_keys):
        key = key.strip()
        if key:
            check_api(f"Cohere Key {i+1}", key, "https://api.cohere.com/v1/models")
            
    # CLOUDFLARE
    print("\n" + "-" * 50)
    print("Testing CLOUDFLARE Keys")
    print("-" * 50)
    for i in range(1, 6):
        account_id = env.get(f"CLOUDFLARE_ACCOUNT_ID_{i}")
        api_key = env.get(f"CLOUDFLARE_API_KEY_{i}")
        if account_id and api_key:
            account_id = account_id.strip()
            api_key = api_key.strip()
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/models/search"
            check_api(f"Cloudflare Key {i}", api_key, url)
            
if __name__ == "__main__":
    main()
