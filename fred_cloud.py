"""
FRED v2.0 - Cloud AI Verbindung
Unterstützt: Ollama (lokal/cloud), OpenAI-Style APIs
"""

import json
import urllib.request
import urllib.error


def get_provider_info():
    try:
        from fred_settings import get_provider, get_model, get_api_key, get_base_url, get_api_style, PROVIDERS
        provider = get_provider()
        info = PROVIDERS.get(provider, {})
        return {
            "provider": provider,
            "name": info.get("name", provider),
            "base_url": get_base_url(),
            "model": get_model(),
            "api_key": get_api_key(),
            "api_style": get_api_style(),
            "needs_key": info.get("needs_key", True)
        }
    except Exception as e:
        return {"error": str(e)}


def chat(prompt, system="Du bist Fred, ein hilfreicher deutscher AI-Assistent.", history=None):
    # Wenn prompt eine Liste ist (messages), extrahiere
    if isinstance(prompt, list):
        history = prompt[:-1] if len(prompt) > 1 else None
        prompt = prompt[-1]["content"] if prompt else ""
    try:
        info = get_provider_info()
        if "error" in info:
            return f"Fehler: {info['error']}"

        api_style = info.get("api_style", "openai")
        base_url = info["base_url"].rstrip("/")
        model = info["model"]
        api_key = info.get("api_key", "")

        if api_style == "ollama":
            return _chat_ollama(base_url, model, prompt, system, history, api_key)
        else:
            return _chat_openai(base_url, model, prompt, system, history, api_key)

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:300]
        except:
            pass
        return f"Fehler: HTTP {e.code} - {e.reason}\n{body}"
    except urllib.error.URLError as e:
        return f"Fehler: Keine Verbindung - {e.reason}"
    except Exception as e:
        return f"Fehler: {e}"


def _chat_ollama(base_url, model, prompt, system, history, api_key=""):
    """Ollama API - lokal und ollama.com cloud"""
    url = f"{base_url}/api/chat"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    data = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False
    }).encode()

    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")

    # Cloud Auth - Bearer Token für ollama.com
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read().decode())

    return result.get("message", {}).get("content", "Keine Antwort")


def _chat_openai(base_url, model, prompt, system, history, api_key=""):
    """OpenAI-kompatible API (Groq, Mistral, OpenRouter etc.)"""
    url = f"{base_url}/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    data = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }).encode()

    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read().decode())

    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print("Test...")
    r = chat("Sage kurz Hallo!")
    print(r)
