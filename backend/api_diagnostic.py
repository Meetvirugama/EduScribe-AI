import os
import json
import urllib.request
import urllib.error
import time


TIMEOUT = 30

TEST_PROMPT = "What is Machine Learning? Answer in one sentence."


# ============================================================
# ENV
# ============================================================

def load_env(filepath):
    env = {}

    if not os.path.exists(filepath):
        print(f"❌ .env not found: {filepath}")
        return env

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)

                env[key.strip()] = (
                    value.strip()
                    .strip('"')
                    .strip("'")
                )

    return env


# ============================================================
# HTTP
# ============================================================

def http_request(url, method="GET", headers=None, data=None):

    headers = headers or {}
    
    if "User-Agent" not in headers:
        headers["User-Agent"] = "curl/8.0"

    encoded_data = None

    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        headers=headers,
        data=encoded_data,
        method=method
    )

    try:

        start = time.perf_counter()

        with urllib.request.urlopen(
            req,
            timeout=TIMEOUT
        ) as response:

            body = response.read().decode("utf-8")

            latency = (
                time.perf_counter() - start
            ) * 1000

            return {
                "success": True,
                "status": response.status,
                "body": body,
                "latency_ms": round(latency, 2),
                "error": None
            }

    except urllib.error.HTTPError as e:

        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = ""

        return {
            "success": False,
            "status": e.code,
            "body": body,
            "latency_ms": None,
            "error": "HTTP_ERROR"
        }

    except Exception as e:

        return {
            "success": False,
            "status": None,
            "body": "",
            "latency_ms": None,
            "error": str(e)
        }


# ============================================================
# GEMINI
# ============================================================

def gemini_list_models(key):

    print("\n  Getting Gemini models...")

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models?key=" + key
    )

    result = http_request(url)

    if not result["success"]:

        print(
            f"  ❌ Cannot list models "
            f"(HTTP {result['status']})"
        )

        print_error(result["body"])

        return []

    try:
        data = json.loads(result["body"])

    except Exception:
        print("  ❌ Invalid JSON response")
        return []

    models = data.get("models", [])

    print(f"  Found {len(models)} Gemini models.")

    available = []

    for model in models:

        name = model.get("name", "")
        display_name = model.get(
            "displayName",
            ""
        )

        methods = model.get(
            "supportedGenerationMethods",
            []
        )

        base_model = model.get(
            "baseModelId",
            ""
        )

        if "generateContent" in methods:

            available.append({
                "name": name,
                "display_name": display_name,
                "base_model": base_model,
                "methods": methods,
                "input_limit": model.get(
                    "inputTokenLimit"
                ),
                "output_limit": model.get(
                    "outputTokenLimit"
                )
            })

    print(
        f"  Models supporting generateContent: "
        f"{len(available)}"
    )

    for i, model in enumerate(
        available,
        1
    ):

        print(
            f"    {i}. "
            f"{model['name']}"
        )

    return available


def gemini_test_model(key, model_name):

    # model_name returned by models.list is:
    # models/xxxxx

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/"
        f"{model_name}:generateContent"
        f"?key={key}"
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

    result = http_request(
        url,
        method="POST",
        headers=headers,
        data=data
    )

    if result["success"]:

        try:

            response = json.loads(
                result["body"]
            )

            candidates = response.get(
                "candidates",
                []
            )

            if candidates:

                print(
                    f"  ✅ MODEL WORKING: "
                    f"{model_name}"
                )

                print(
                    f"     Latency: "
                    f"{result['latency_ms']} ms"
                )

                return True

            print(
                f"  ❌ Model returned "
                f"no candidates"
            )

        except Exception:

            print(
                "  ❌ Invalid generation response"
            )

    else:

        print(
            f"  ❌ MODEL FAILED: "
            f"{model_name}"
        )

        print(
            f"     HTTP: "
            f"{result['status']}"
        )

        print_error(result["body"])

    return False


def test_gemini_key(key, number):

    print()
    print("=" * 60)
    print(f"GEMINI KEY {number}")
    print("=" * 60)

    models = gemini_list_models(key)

    if not models:

        print()
        print("❌ GEMINI KEY STATUS: NOT USABLE")
        return False

    print()
    print("Testing available models...")

    for model in models:

        if gemini_test_model(
            key,
            model["name"]
        ):
            print()
            print(
                "✅ GEMINI KEY STATUS: WORKING"
            )

            print(
                f"   Working model: "
                f"{model['name']}"
            )

            return True

    print()
    print(
        "⚠️ GEMINI KEY AUTHENTICATED, "
        "BUT NO MODEL GENERATED SUCCESSFULLY"
    )

    return False


# ============================================================
# GROQ
# ============================================================

def groq_list_models(key):

    print("\n  Getting Groq models...")

    url = (
        "https://api.groq.com/"
        "openai/v1/models"
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    result = http_request(
        url,
        method="GET",
        headers=headers
    )

    if not result["success"]:

        print(
            f"  ❌ Cannot list models "
            f"(HTTP {result['status']})"
        )

        print_error(result["body"])

        return []

    try:

        data = json.loads(
            result["body"]
        )

    except Exception:

        print("  ❌ Invalid JSON response")
        return []

    models = data.get(
        "data",
        []
    )

    print(
        f"  Found {len(models)} Groq models."
    )

    for i, model in enumerate(
        models,
        1
    ):

        print(
            f"    {i}. "
            f"{model.get('id')}"
        )

    return models


def groq_test_model(key, model_id):

    url = (
        "https://api.groq.com/"
        "openai/v1/chat/completions"
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model_id,

        "messages": [
            {
                "role": "user",
                "content": TEST_PROMPT
            }
        ],

        "max_tokens": 50
    }

    result = http_request(
        url,
        method="POST",
        headers=headers,
        data=data
    )

    if result["success"]:

        try:

            response = json.loads(
                result["body"]
            )

            choices = response.get(
                "choices",
                []
            )

            if choices:

                print(
                    f"  ✅ MODEL WORKING: "
                    f"{model_id}"
                )

                print(
                    f"     Latency: "
                    f"{result['latency_ms']} ms"
                )

                return True

        except Exception:
            pass

        print(
            "  ❌ Invalid generation response"
        )

    else:

        print(
            f"  ❌ MODEL FAILED: "
            f"{model_id}"
        )

        print(
            f"     HTTP: "
            f"{result['status']}"
        )

        print_error(result["body"])

    return False


def test_groq_key(key, number):

    print()
    print("=" * 60)
    print(f"GROQ KEY {number}")
    print("=" * 60)

    models = groq_list_models(key)

    if not models:

        print()
        print(
            "❌ GROQ KEY STATUS: "
            "NOT USABLE / ACCESS PROBLEM"
        )

        return False

    print()
    print("Testing available models...")

    for model in models:

        model_id = model.get("id")

        if not model_id:
            continue

        # Skip obvious non-chat/audio/embedding models
        # if desired. For now, test every model until
        # one successfully generates.

        if groq_test_model(
            key,
            model_id
        ):

            print()
            print(
                "✅ GROQ KEY STATUS: WORKING"
            )

            print(
                f"   Working model: "
                f"{model_id}"
            )

            return True

    print()
    print(
        "⚠️ GROQ KEY AUTHENTICATED, "
        "BUT NO MODEL GENERATED SUCCESSFULLY"
    )

    return False


# ============================================================
# ERROR DISPLAY
# ============================================================

def print_error(body):

    if not body:
        return

    try:

        data = json.loads(body)

        if "error" in data:

            error = data["error"]

            if isinstance(error, dict):

                message = error.get(
                    "message"
                )

                error_type = error.get(
                    "type"
                )

                code = error.get(
                    "code"
                )

                if error_type:
                    print(
                        f"     Type: "
                        f"{error_type}"
                    )

                if code:
                    print(
                        f"     Code: "
                        f"{code}"
                    )

                if message:
                    print(
                        f"     Message: "
                        f"{message}"
                    )

                return

    except Exception:
        pass

    print(
        f"     Response: "
        f"{body[:500]}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    env_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        ".env"
    )

    env = load_env(env_path)

    print()
    print("=" * 60)
    print("       GEMINI + GROQ API DIAGNOSTIC")
    print("=" * 60)

    print()
    print("Test prompt:")
    print(TEST_PROMPT)

    # ========================================================
    # GEMINI
    # ========================================================

    gemini_keys = [
        k.strip()
        for k in env.get(
            "GEMINI_API_KEYS",
            ""
        ).split(",")
        if k.strip()
    ]

    print()
    print(
        f"Gemini keys found: "
        f"{len(gemini_keys)}"
    )

    gemini_results = []

    for i, key in enumerate(
        gemini_keys,
        1
    ):

        result = test_gemini_key(
            key,
            i
        )

        gemini_results.append(result)

        time.sleep(1)

    # ========================================================
    # GROQ
    # ========================================================

    groq_keys = [
        k.strip()
        for k in env.get(
            "GROQ_API_KEYS",
            ""
        ).split(",")
        if k.strip()
    ]

    print()
    print(
        f"Groq keys found: "
        f"{len(groq_keys)}"
    )

    groq_results = []

    for i, key in enumerate(
        groq_keys,
        1
    ):

        result = test_groq_key(
            key,
            i
        )

        groq_results.append(result)

        time.sleep(1)

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(
        f"Gemini: "
        f"{sum(gemini_results)}/"
        f"{len(gemini_results)} working"
    )

    print(
        f"Groq:   "
        f"{sum(groq_results)}/"
        f"{len(groq_results)} working"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
