import os
import json
import urllib.request
import urllib.error
import time


# =========================
# CONFIG
# =========================

TEST_PROMPT = "What is Machine Learning? Explain it briefly in 2-3 sentences."

TIMEOUT = 30


# =========================
# ENV LOADER
# =========================

def load_env(filepath):
    env = {}

    if not os.path.exists(filepath):
        print(f"ERROR: {filepath} not found.")
        return env

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")

    return env


# =========================
# GENERIC HTTP REQUEST
# =========================

def request(url, headers, data):
    try:
        req = urllib.request.Request(
            url,
            headers=headers,
            data=json.dumps(data).encode("utf-8"),
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8")
            return True, response.status, body

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = ""

        return False, e.code, body

    except Exception as e:
        return False, None, str(e)


# =========================
# GROQ
# =========================

def test_groq(key):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        # Use a currently available Groq model from your account.
        "model": "openai/gpt-oss-20b",
        "messages": [
            {
                "role": "user",
                "content": TEST_PROMPT
            }
        ],
        "max_tokens": 100
    }

    return request(url, headers, data)


# =========================
# GEMINI
# =========================

def test_gemini(key):
    try:
        # First discover models available to this key.
        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models?key=" + key
        )

        req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            models = json.loads(response.read().decode())

        available = []

        for model in models.get("models", []):
            methods = model.get("supportedGenerationMethods", [])

            if "generateContent" in methods:
                name = model.get("name")

                if name:
                    available.append(name)

        if not available:
            return False, None, "No generateContent model available"

        # Prefer Flash model.
        preferred = None

        for model in available:
            if "flash" in model.lower():
                preferred = model
                break

        model_name = preferred or available[0]

        url = (
            f"https://generativelanguage.googleapis.com/"
            f"v1beta/{model_name}:generateContent?key={key}"
        )

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": TEST_PROMPT
                        }
                    ]
                }
            ]
        }

        return request(url, headers, data)

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = ""

        return False, e.code, body

    except Exception as e:
        return False, None, str(e)


# =========================
# OPENROUTER
# =========================

def test_openrouter(key):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        # Change this if this free model is unavailable.
        "model": "openrouter/free",
        "messages": [
            {
                "role": "user",
                "content": TEST_PROMPT
            }
        ],
        "max_tokens": 100
    }

    return request(url, headers, data)


# =========================
# COHERE
# =========================

def test_cohere(key):
    url = "https://api.cohere.com/v2/chat"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "command-a-03-2025",
        "messages": [
            {
                "role": "user",
                "content": TEST_PROMPT
            }
        ],
        "max_tokens": 100
    }

    return request(url, headers, data)


# =========================
# CLOUDFLARE
# =========================

def test_cloudflare(account_id, key):
    # Current model must exist in your Workers AI account.
    model = "@cf/meta/llama-3.1-8b-instruct"

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{model}"
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": TEST_PROMPT
            }
        ]
    }

    return request(url, headers, data)


# =========================
# HUGGING FACE
# =========================

def test_huggingface(key):
    url = (
        "https://router.huggingface.co/"
        "v1/chat/completions"
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": TEST_PROMPT
            }
        ],
        "max_tokens": 100
    }

    return request(url, headers, data)


# =========================
# RESULT CHECK
# =========================

def is_success(success, status, body):
    if not success:
        return False

    if status != 200:
        return False

    if not body:
        return False

    try:
        data = json.loads(body)

        # Basic check that the provider returned something.
        if "error" in data:
            return False

        return True

    except Exception:
        return False


def print_result(provider, number, success, status, body):
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_health_responses")
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{provider}_Key_{number}.txt")
    
    try:
        if body:
            with open(filename, "w", encoding="utf-8") as f:
                try:
                    # Try to format as nice JSON if it is JSON
                    parsed = json.loads(body)
                    f.write(json.dumps(parsed, indent=4))
                except json.JSONDecodeError:
                    f.write(body)
    except Exception:
        pass

    if is_success(success, status, body):
        print(f"{provider:<15} Key {number:<3} ✅ WORKING (Saved to {os.path.basename(filename)})")
    else:
        print(f"{provider:<15} Key {number:<3} ❌ NOT WORKING (Saved to {os.path.basename(filename)})")


# =========================
# MAIN
# =========================

def main():

    env_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".env"
    )

    env = load_env(env_path)

    print()
    print("=" * 55)
    print("             API HEALTH CHECK")
    print("=" * 55)
    print()
    print("Test question:")
    print(TEST_PROMPT)
    print()

    # -------------------------
    # GROQ
    # -------------------------

    groq_keys = [
        k.strip()
        for k in env.get("GROQ_API_KEYS", "").split(",")
        if k.strip()
    ]

    for i, key in enumerate(groq_keys, 1):
        success, status, body = test_groq(key)
        print_result("Groq", i, success, status, body)
        time.sleep(0.5)

    # -------------------------
    # GEMINI
    # -------------------------

    gemini_keys = [
        k.strip()
        for k in env.get("GEMINI_API_KEYS", "").split(",")
        if k.strip()
    ]

    for i, key in enumerate(gemini_keys, 1):
        success, status, body = test_gemini(key)
        print_result("Gemini", i, success, status, body)
        time.sleep(0.5)

    # -------------------------
    # OPENROUTER
    # -------------------------

    openrouter_keys = [
        k.strip()
        for k in env.get("OPENROUTER_API_KEYS", "").split(",")
        if k.strip()
    ]

    for i, key in enumerate(openrouter_keys, 1):
        success, status, body = test_openrouter(key)
        print_result("OpenRouter", i, success, status, body)
        time.sleep(0.5)

    # -------------------------
    # COHERE
    # -------------------------

    cohere_keys = [
        k.strip()
        for k in env.get("COHERE_API_KEYS", "").split(",")
        if k.strip()
    ]

    for i, key in enumerate(cohere_keys, 1):
        success, status, body = test_cohere(key)
        print_result("Cohere", i, success, status, body)
        time.sleep(0.5)

    # -------------------------
    # CLOUDFLARE
    # -------------------------

    for i in range(1, 6):

        account_id = env.get(
            f"CLOUDFLARE_ACCOUNT_ID_{i}"
        )

        key = env.get(
            f"CLOUDFLARE_API_KEY_{i}"
        )

        if account_id and key:
            success, status, body = test_cloudflare(
                account_id.strip(),
                key.strip()
            )

            print_result(
                "Cloudflare",
                i,
                success,
                status,
                body
            )

            time.sleep(0.5)

    # -------------------------
    # HUGGING FACE
    # -------------------------

    hf_keys = [
        k.strip()
        for k in env.get("HUGGINGFACE_API_KEYS", "").split(",")
        if k.strip()
    ]

    for i, key in enumerate(hf_keys, 1):
        success, status, body = test_huggingface(key)
        print_result("HuggingFace", i, success, status, body)
        time.sleep(0.5)

    print()
    print("=" * 55)
    print("                  DONE")
    print("=" * 55)


if __name__ == "__main__":
    main()
