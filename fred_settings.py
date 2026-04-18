"""
FRED v2.0 - Einstellungen & Provider-Verwaltung
"""

import os
import json
import time

CONFIG_FILE = os.path.expanduser("~/fred/fred_config.json")

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
R = "\033[0m"

PROVIDERS = {
    "ollama_local": {
        "name": "Ollama Lokal",
        "base_url": "http://localhost:11434",
        "default_model": "llama3.1",
        "needs_key": False,
        "api_style": "ollama"
    },
    "ollama_cloud": {
        "name": "Ollama Cloud",
        "base_url": "https://api.ollama.com",
        "default_model": "llama3.1",
        "needs_key": True,
        "api_style": "ollama"
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-3.5-turbo",
        "needs_key": True,
        "api_style": "openai"
    },
    "groq": {
        "name": "Groq (Gratis)",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.1-8b-instant",
        "needs_key": True,
        "api_style": "openai"
    },
    "mistral": {
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-small-latest",
        "needs_key": True,
        "api_style": "openai"
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "meta-llama/llama-3.1-8b-instruct:free",
        "needs_key": True,
        "api_style": "openai"
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Llama-3-8b-chat-hf",
        "needs_key": True,
        "api_style": "openai"
    }
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_provider():
    config = load_config()
    return config.get("provider", "ollama_local")


def get_model():
    config = load_config()
    provider = get_provider()
    default = PROVIDERS.get(provider, {}).get("default_model", "llama3.1")
    return config.get("model", default)


def get_api_key():
    config = load_config()
    return config.get("api_key", "")


def get_base_url():
    config = load_config()
    provider = get_provider()
    default = PROVIDERS.get(provider, {}).get("base_url", "")
    return config.get("base_url", default)


def get_api_style():
    provider = get_provider()
    return PROVIDERS.get(provider, {}).get("api_style", "openai")


def clear():
    os.system('clear')


def header(title="Einstellungen"):
    width = os.get_terminal_size().columns
    print(f"\n{MAGENTA}{BOLD}{'═' * width}")
    print(f"  ⚙️  {title}")
    print(f"{'═' * width}{R}")


def show_current():
    provider = get_provider()
    info = PROVIDERS.get(provider, {})
    key = get_api_key()
    print(f"\n  {BOLD}Aktuelle Konfiguration:{R}")
    print(f"    Provider:  {GREEN}{info.get('name', provider)}{R}")
    print(f"    Modell:    {CYAN}{get_model()}{R}")
    print(f"    Base URL:  {DIM}{get_base_url()}{R}")
    print(f"    API Style: {DIM}{get_api_style()}{R}")
    if info.get("needs_key", True):
        status = f"{GREEN}✅ gesetzt{R}" if key else f"{RED}❌ fehlt{R}"
        print(f"    API Key:   {status}")
    else:
        print(f"    API Key:   {DIM}nicht benötigt{R}")


def choose_provider():
    clear()
    header("Provider wählen")

    providers = list(PROVIDERS.keys())
    for i, key in enumerate(providers, 1):
        info = PROVIDERS[key]
        print(f"    {CYAN}{i}{R}. {info['name']}")
        print(f"       {DIM}{info['default_model']} • {info['base_url']}{R}")

    print(f"\n    {YELLOW}0{R}. Zurück")

    try:
        choice = input(f"\n  Wahl: {CYAN}").strip()
        print(R, end="")
        idx = int(choice) - 1
        if 0 <= idx < len(providers):
            selected = providers[idx]
            info = PROVIDERS[selected]
            config = load_config()
            config["provider"] = selected
            config["model"] = info["default_model"]
            config["base_url"] = info["base_url"]

            if info["needs_key"]:
                current_key = config.get("api_key", "")
                print(f"\n  API Key {'ändern' if current_key else 'eingeben'}:")
                key = input(f"  {CYAN}").strip()
                print(R, end="")
                if key:
                    config["api_key"] = key
            else:
                config.pop("api_key", None)

            save_config(config)
            print(f"\n  {GREEN}✅ {info['name']} konfiguriert!{R}")
            time.sleep(1)
    except (ValueError, IndexError):
        pass


def change_model():
    clear()
    header("Modell ändern")
    show_current()

    provider = get_provider()
    style = get_api_style()
    base = get_base_url()
    key = get_api_key()

    # Live-Modelle abrufen
    models = []
    try:
        import requests
        if style == "ollama":
            r = requests.get(f"{base}/api/tags", timeout=5)
            if r.ok:
                models = [m['name'] for m in r.json().get('models', [])]
        else:
            headers = {"Authorization": f"Bearer {key}"}
            r = requests.get(f"{base}/models", headers=headers, timeout=5)
            if r.ok:
                models = [m['id'] for m in r.json().get('data', [])]
    except:
        pass

    if models:
        models.sort()
        print(f"\n  {BOLD}Verfügbare Modelle ({len(models)}):{R}\n")
        for i, m in enumerate(models[:30], 1):
            marker = " 👈" if m == get_model() else ""
            print(f"  {DIM}{i:3}.{R} {m}{GREEN}{marker}{R}")
        if len(models) > 30:
            print(f"\n  {DIM}... und {len(models)-30} weitere{R}")
        print(f"\n  Nummer oder Name eingeben (leer = abbrechen):")
    else:
        print(f"\n  {YELLOW}⚠ Konnte keine Modelle abrufen{R}")
        print(f"\n  Modellname eingeben (leer = abbrechen):")

    choice = input(f"  {CYAN}").strip()
    print(R, end="")

    if not choice:
        return

    # Nummer oder Name?
    if choice.isdigit() and models:
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            choice = models[idx]
        else:
            print(f"\n  {RED}❌ Ungültige Nummer{R}")
            time.sleep(1)
            return

    config = load_config()
    config["model"] = choice
    save_config(config)
    print(f"\n  {GREEN}✅ Modell: {choice}{R}")
    time.sleep(1)


def change_api_key():
    clear()
    header("API Key ändern")

    key = input(f"\n  Neuer API Key: {CYAN}").strip()
    print(R, end="")

    if key:
        config = load_config()
        config["api_key"] = key
        save_config(config)
        print(f"\n  {GREEN}✅ API Key gespeichert!{R}")
        time.sleep(1)


def test_connection():
    clear()
    header("Verbindungstest")
    show_current()

    print(f"\n  {YELLOW}Teste Verbindung...{R}")

    try:
        from fred_cloud import chat
        response = chat("Sage nur: Hallo, ich bin Fred!", system="Antworte kurz auf Deutsch.")
        if response and not response.startswith("Fehler"):
            print(f"\n  {GREEN}✅ Verbindung erfolgreich!{R}")
            print(f"  {DIM}Antwort: {response[:100]}{R}")
        else:
            print(f"\n  {RED}❌ {response}{R}")
    except Exception as e:
        print(f"\n  {RED}❌ Fehler: {e}{R}")

    input(f"\n  {DIM}Enter...{R}")


def settings_menu():
    while True:
        clear()
        header("Einstellungen")
        show_current()

        print(f"\n  {CYAN}1{R}. Provider wählen")
        print(f"  {CYAN}2{R}. Modell ändern")
        print(f"  {CYAN}3{R}. API Key ändern")
        print(f"  {CYAN}4{R}. Verbindung testen")
        print(f"\n  {YELLOW}0{R}. Zurück")

        choice = input(f"\n  Wahl: {CYAN}").strip()
        print(R, end="")

        if choice == "1":
            choose_provider()
        elif choice == "2":
            change_model()
        elif choice == "3":
            change_api_key()
        elif choice == "4":
            test_connection()
        elif choice == "0":
            break


if __name__ == "__main__":
    settings_menu()

def get_setting(key, default=None):
    config = load_config()
    return config.get(key, default)

def save_setting(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
