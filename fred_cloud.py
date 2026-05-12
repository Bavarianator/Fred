"""
FRED v2.0 - Cloud AI Verbindung
Unterstützt: Ollama (lokal/cloud), OpenAI-Style APIs
"""

import json
import urllib.request
import urllib.error
import time


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


def quick_ask(prompt, system="Du bist Fred, ein hilfreicher deutscher AI-Assistent."):
    """
    Schnelle einzelne Anfrage ohne Chat-Verlauf
    
    Args:
        prompt: Die Frage/Prompt
        system: System-Prompt (optional)
    
    Returns:
        dict mit {'ok': bool, 'content': str, 'error': str, 'tokens_in': int, 'tokens_out': int}
    """
    try:
        info = get_provider_info()
        if "error" in info:
            return {"ok": False, "error": f"Konfigurationsfehler: {info['error']}", "content": ""}
        
        api_style = info.get("api_style", "openai")
        base_url = info["base_url"].rstrip("/")
        model = info["model"]
        api_key = info.get("api_key", "")
        
        start_time = time.time()
        
        if api_style == "ollama":
            result = _chat_ollama(base_url, model, prompt, system, None, api_key)
            # Ollama liefert keine Token-Infos im non-streaming Modus
            tokens_out = len(result.split()) * 1.3  # Schätzung
        else:
            result = _chat_openai(base_url, model, prompt, system, None, api_key)
            tokens_out = len(result.split()) * 1.3  # Schätzung
        
        elapsed = time.time() - start_time
        
        return {
            "ok": True,
            "content": result,
            "tokens_in": len(prompt.split()) * 1.3,  # Schätzung
            "tokens_out": int(tokens_out),
            "elapsed": round(elapsed, 2)
        }
        
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:300]
        except:
            pass
        return {"ok": False, "error": f"HTTP {e.code} - {e.reason}\n{body}", "content": ""}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Keine Verbindung: {e.reason}", "content": ""}
    except Exception as e:
        return {"ok": False, "error": str(e), "content": ""}



def chat(prompt, system="Du bist Fred, ein hilfreicher deutscher AI-Assistent.", history=None):
    """Chat mit Verlauf"""
    # Wenn prompt eine Liste ist (messages), extrahiere
    if isinstance(prompt, list):
        history = prompt[:-1] if len(prompt) > 1 else None
        prompt = prompt[-1]["content"] if prompt else ""
    
    # Input validation
    if not prompt or not prompt.strip():
        return "Fehler: Leerer Prompt"
    
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
    except TimeoutError:
        return "Fehler: Zeitüberschreitung bei der Anfrage"
    except Exception as e:
        return f"Fehler: {type(e).__name__} - {e}"


def _chat_ollama(base_url, model, prompt, system, history, api_key=""):
    """Ollama API - lokal und ollama.com cloud"""
    if not base_url or not model:
        raise ValueError("Base-URL und Modell müssen angegeben werden")
    
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

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode())
        return result.get("message", {}).get("content", "Keine Antwort")
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()[:500]
        except:
            pass
        raise Exception(f"Ollama API Fehler {e.code}: {e.reason}\n{error_body}")


def _chat_openai(base_url, model, prompt, system, history, api_key=""):
    """OpenAI-kompatible API (Groq, Mistral, OpenRouter etc.)"""
    if not base_url or not model:
        raise ValueError("Base-URL und Modell müssen angegeben werden")
    
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

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode())
        
        if "choices" not in result or len(result["choices"]) == 0:
            raise Exception("Ungültige API-Antwort: Keine Choices")
        
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()[:500]
        except:
            pass
        raise Exception(f"API Fehler {e.code}: {e.reason}\n{error_body}")


if __name__ == "__main__":
    print("Test...")
    r = chat("Sage kurz Hallo!")
    print(r)
