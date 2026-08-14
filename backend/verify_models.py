import os
import re
import urllib.request
import json
import time

def load_env(filepath):
    if not os.path.exists(filepath):
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

GROQ_KEY = get_key("GROQ")
GEMINI_KEY = get_key("GEMINI")
COHERE_KEY = get_key("COHERE")
OPENROUTER_KEY = get_key("OPENROUTER")

def test_groq(model):
    url = "https://api.groq.com/openai/v1/chat/completions"
    data = {"model": model, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}
    req = urllib.request.Request(url, method="POST", headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json", "User-Agent": "curl/8.0"}, data=json.dumps(data).encode("utf-8"))
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return True, "OK"
    except Exception as e:
        return False, str(e)

def test_gemini(model):
    # Model string comes as "models/gemini-..." or just "gemini-..."
    model_name = model if model.startswith("models/") else f"models/{model}"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_KEY}"
    data = {"contents": [{"parts":[{"text": "Hi"}]}]}
    req = urllib.request.Request(url, method="POST", headers={"Content-Type": "application/json"}, data=json.dumps(data).encode("utf-8"))
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return True, "OK"
    except Exception as e:
        return False, str(e)

def test_cohere(model):
    url = "https://api.cohere.ai/v1/chat"
    data = {"model": model, "message": "Hi"}
    req = urllib.request.Request(url, method="POST", headers={"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json", "accept": "application/json"}, data=json.dumps(data).encode("utf-8"))
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return True, "OK"
    except Exception as e:
        return False, str(e)

def test_openrouter(model):
    url = "https://openrouter.ai/api/v1/chat/completions"
    data = {"model": model, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}
    req = urllib.request.Request(url, method="POST", headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}, data=json.dumps(data).encode("utf-8"))
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return True, "OK"
    except Exception as e:
        return False, str(e)

def main():
    md_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../docs/available_models.md")
    with open(md_file, "r") as f:
        lines = f.readlines()

    current_provider = None
    output_lines = []

    print("Testing models one by one. This may take a few minutes to respect rate limits...\n")

    for line in lines:
        if line.startswith("## "):
            current_provider = line.strip()
            output_lines.append(line)
            continue
        
        match = re.match(r"^- (.+)$", line.strip())
        if match:
            model_raw = match.group(1)
            
            if "Cohere" in current_provider:
                # Force retest for Cohere
                model = model_raw.split("*(Failed")[0].replace("✅", "").replace("❌", "").replace("**", "").strip()
            else:
                # If already tested and not Cohere, skip
                if "✅" in model_raw or "❌" in model_raw:
                    output_lines.append(line)
                    continue
                model = model_raw.strip()
            
            print(f"Testing {current_provider} -> {model}...", end=" ", flush=True)

            success = False
            msg = ""
            
            if "Groq" in current_provider:
                success, msg = test_groq(model)
                time.sleep(1) # rate limit mitigation
            elif "Gemini" in current_provider:
                success, msg = test_gemini(model)
                time.sleep(2) # 15 RPM mitigation
            elif "Cohere" in current_provider:
                success, msg = test_cohere(model)
                time.sleep(1)
            elif "OpenRouter" in current_provider:
                success, msg = test_openrouter(model)
                time.sleep(1)
            else:
                success, msg = False, "Unknown provider"

            if success:
                print("✅ Working")
                output_lines.append(f"- ✅ **{model}**\n")
            else:
                # Clean up error message for markdown
                err = msg.replace('\n', ' ').replace('\r', '')
                print(f"❌ Failed: {err}")
                output_lines.append(f"- ❌ {model} *(Failed: {err})*\n")
        else:
            output_lines.append(line)

    with open(md_file, "w") as f:
        f.writelines(output_lines)

    print("\nDone! Updated docs/available_models.md")

if __name__ == "__main__":
    main()
