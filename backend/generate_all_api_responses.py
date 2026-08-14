import os
import json
import urllib.request
import urllib.error
import time

def load_env(filepath):
    env_vars = {}
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return env_vars
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

def call_groq(key, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"model": "llama3-8b-8192", "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode('utf-8'))
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error: {e}"

def call_gemini(key, prompt):
    # First, list models to find an available one that supports generateContent
    url_models = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        req = urllib.request.Request(url_models)
        with urllib.request.urlopen(req) as response:
            models_data = json.loads(response.read().decode())
            available_models = [m['name'] for m in models_data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            if not available_models:
                return "Error: No supported models found for generateContent."
            
            # Use the first available model (usually models/gemini-1.5-flash or models/gemini-pro)
            model_name = available_models[0]
            
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={key}"
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            req2 = urllib.request.Request(url, headers={"Content-Type": "application/json"}, data=json.dumps(data).encode('utf-8'))
            with urllib.request.urlopen(req2) as res2:
                res_data = json.loads(res2.read().decode())
                return res_data['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error: {e}"

def call_openrouter(key, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"model": "meta-llama/llama-3-8b-instruct:free", "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode('utf-8'))
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error: {e}"

def call_cohere(key, prompt):
    url = "https://api.cohere.ai/v1/chat"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"message": prompt, "model": "command-r"}
    req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode('utf-8'))
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())['text']
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error: {e}"

def call_cloudflare(account_id, key, prompt):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3-8b-instruct"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode('utf-8'))
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())['result']['response']
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error: {e}"

def call_huggingface(key, prompt):
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"inputs": f"<s>[INST] {prompt} [/INST]"}
    req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode('utf-8'))
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())[0]['generated_text']
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error: {e}"

def main():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    env = load_env(env_path)
    
    output_dir = os.path.join(os.path.dirname(__file__), "api_responses_all_keys")
    os.makedirs(output_dir, exist_ok=True)
    
    prompt = "Give me ML mathematics equations. Include 3-5 different mathematical equations commonly used in Machine Learning with brief explanations."
    
    print(f"Generating responses across all API providers and saving to {output_dir}")
    print("-" * 50)
    
    # GROQ
    groq_keys = [k.strip() for k in env.get("GROQ_API_KEYS", "").split(",") if k.strip()]
    for i, key in enumerate(groq_keys):
        print(f"Querying Groq Key {i+1}...")
        resp = call_groq(key, prompt)
        with open(os.path.join(output_dir, f"Groq_Key_{i+1}.md"), "w", encoding="utf-8") as f:
            f.write(f"# Groq Key {i+1} Response\n\n{resp}")
        time.sleep(1)

    # GEMINI
    gemini_keys = [k.strip() for k in env.get("GEMINI_API_KEYS", "").split(",") if k.strip()]
    for i, key in enumerate(gemini_keys):
        print(f"Querying Gemini Key {i+1}...")
        resp = call_gemini(key, prompt)
        with open(os.path.join(output_dir, f"Gemini_Key_{i+1}.md"), "w", encoding="utf-8") as f:
            f.write(f"# Gemini Key {i+1} Response\n\n{resp}")
        time.sleep(1)

    # OPENROUTER
    or_keys = [k.strip() for k in env.get("OPENROUTER_API_KEYS", "").split(",") if k.strip()]
    for i, key in enumerate(or_keys):
        print(f"Querying OpenRouter Key {i+1}...")
        resp = call_openrouter(key, prompt)
        with open(os.path.join(output_dir, f"OpenRouter_Key_{i+1}.md"), "w", encoding="utf-8") as f:
            f.write(f"# OpenRouter Key {i+1} Response\n\n{resp}")
        time.sleep(1)

    # COHERE
    cohere_keys = [k.strip() for k in env.get("COHERE_API_KEYS", "").split(",") if k.strip()]
    for i, key in enumerate(cohere_keys):
        print(f"Querying Cohere Key {i+1}...")
        resp = call_cohere(key, prompt)
        with open(os.path.join(output_dir, f"Cohere_Key_{i+1}.md"), "w", encoding="utf-8") as f:
            f.write(f"# Cohere Key {i+1} Response\n\n{resp}")
        time.sleep(1)
        
    # CLOUDFLARE
    for i in range(1, 6):
        account_id = env.get(f"CLOUDFLARE_ACCOUNT_ID_{i}")
        key = env.get(f"CLOUDFLARE_API_KEY_{i}")
        if account_id and key:
            print(f"Querying Cloudflare Key {i}...")
            resp = call_cloudflare(account_id.strip(), key.strip(), prompt)
            with open(os.path.join(output_dir, f"Cloudflare_Key_{i}.md"), "w", encoding="utf-8") as f:
                f.write(f"# Cloudflare Key {i} Response\n\n{resp}")
            time.sleep(1)
            
    # HUGGINGFACE
    hf_keys = [k.strip() for k in env.get("HUGGINGFACE_API_KEYS", "").split(",") if k.strip()]
    for i, key in enumerate(hf_keys):
        print(f"Querying HuggingFace Key {i+1}...")
        resp = call_huggingface(key, prompt)
        with open(os.path.join(output_dir, f"HuggingFace_Key_{i+1}.md"), "w", encoding="utf-8") as f:
            f.write(f"# HuggingFace Key {i+1} Response\n\n{resp}")
        time.sleep(1)

    print("-" * 50)
    print("Done generating responses from all API providers!")

if __name__ == "__main__":
    main()
