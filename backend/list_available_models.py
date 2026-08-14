import os
import json
import urllib.request
import asyncio

def load_env(filepath):
    if not os.path.exists(filepath):
        print(f"❌ .env not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_env(env_path)


def get_key(provider_prefix):
    keys = os.environ.get(f"{provider_prefix}_API_KEYS")
    if keys: return keys.split(",")[0]
    return os.environ.get(f"{provider_prefix}_API_KEY")

def fetch_models_groq():
    key = get_key("GROQ")
    if not key: return ["No key found"]
    url = "https://api.groq.com/openai/v1/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["id"] for m in data.get("data", [])]
    except Exception as e:
        return [f"Error: {e}"]

def fetch_models_gemini():
    key = get_key("GEMINI")
    if not key: return ["No key found"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception as e:
        return [f"Error: {e}"]

def fetch_models_cohere():
    key = get_key("COHERE")
    if not key: return ["No key found"]
    url = "https://api.cohere.ai/v1/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        return [f"Error: {e}"]

def fetch_models_openrouter():
    url = "https://openrouter.ai/api/v1/models"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            # Just grab the free ones to avoid listing 200+ models
            free_models = [m["id"] for m in data.get("data", []) if m.get("pricing", {}).get("prompt") == "0"]
            return free_models
    except Exception as e:
        return [f"Error: {e}"]


def main():
    print("# Available Models for Your APIs\n")
    
    print("## Groq Models")
    for m in fetch_models_groq(): print(f"- {m}")
    print()

    print("## Gemini Models (Supports Generation)")
    for m in fetch_models_gemini(): print(f"- {m}")
    print()
    
    print("## Cohere Models")
    for m in fetch_models_cohere(): print(f"- {m}")
    print()

    print("## OpenRouter Free Models")
    for m in fetch_models_openrouter(): print(f"- {m}")
    print()

if __name__ == "__main__":
    main()
