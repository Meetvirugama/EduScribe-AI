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

def call_openrouter(api_key, prompt, index):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Slight variations in temperature
    temperature = 0.5 + (index % 5) * 0.1 
    
    data = {
        "model": "meta-llama/llama-3-8b-instruct:free",  # High quality free model on OpenRouter
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    
    req = urllib.request.Request(url, headers=headers, method="POST", data=json.dumps(data).encode('utf-8'))
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text = res_data['choices'][0]['message']['content']
            return text
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"HTTP Error: {e.code} - {error_msg}")
        return None
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return None

def main():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    env = load_env(env_path)
    
    keys_str = env.get("OPENROUTER_API_KEYS", "")
    or_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    
    if not or_keys:
        print("No OpenRouter keys found in .env file.")
        return

    output_dir = os.path.join(os.path.dirname(__file__), "ml_equations_responses")
    os.makedirs(output_dir, exist_ok=True)
    
    base_prompt = "Give me ML mathematics equations. Include 3-5 different mathematical equations commonly used in Machine Learning with brief explanations."
    
    print(f"Generating 30 API responses using OpenRouter and saving to {output_dir}")
    print("-" * 50)
    
    for i in range(1, 31):
        # Round-robin through available keys
        key = or_keys[i % len(or_keys)]
        print(f"Generating response {i}/30...")
        
        # Variation id
        prompt = f"{base_prompt} (Variation ID: {i})"
        
        response_text = call_openrouter(key, prompt, i)
        
        if response_text:
            filename = os.path.join(output_dir, f"response_{i}.md")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# ML Mathematics Equations - Response {i}\n\n")
                f.write(response_text)
            print(f"✅ Saved to {filename}")
        else:
            print(f"❌ Failed to generate response {i}")
        
        # Small delay
        time.sleep(1)
        
    print("-" * 50)
    print("Done!")

if __name__ == "__main__":
    main()
