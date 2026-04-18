#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════╗
║  FRED v2.0 - Dein Terminal AI Assistent       ║
║  Offline & Cloud • Modular • Leichtgewicht    ║
╚═══════════════════════════════════════════════╝
"""

import os
import sys
import time
from datetime import datetime

# ══════════════════════════════════════════
#  FARBEN
# ══════════════════════════════════════════

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
R = "\033[0m"

VERSION = "2.0"


def clear():
    os.system('clear')


# ══════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════

def show_banner():
    width = os.get_terminal_size().columns

    banner = f"""
{CYAN}{BOLD}
    ███████╗██████╗ ███████╗██████╗ 
    ██╔════╝██╔══██╗██╔════╝██╔══██╗
    █████╗  ██████╔╝█████╗  ██║  ██║
    ██╔══╝  ██╔══██╗██╔══╝  ██║  ██║
    ██║     ██║  ██║███████╗██████╔╝
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝ {R}{DIM}v{VERSION}{R}
"""
    print(banner)
    print(f"{DIM}{'─' * width}{R}")

    # Status-Zeile
    now = datetime.now().strftime('%H:%M')
    day = datetime.now().strftime('%A')
    days_de = {
        'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
        'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag',
        'Sunday': 'Sonntag'
    }
    day_de = days_de.get(day, day)

    # Provider Info
    try:
        from fred_settings import get_provider, get_model, get_api_key, PROVIDERS
        provider = get_provider()
        provider_name = PROVIDERS.get(provider, {}).get("name", provider)
        model = get_model()
        has_key = "✅" if get_api_key() or provider == "ollama_local" else "❌"
        ai_status = f"{provider_name} • {model} {has_key}"
    except:
        ai_status = "Nicht konfiguriert ❌"

    print(f"  {DIM}📅 {day_de}, {now}  │  🤖 {ai_status}{R}")
    print(f"{DIM}{'─' * width}{R}")


# ══════════════════════════════════════════
#  QUICK STATS
# ══════════════════════════════════════════

def quick_stats():
    stats = []

    try:
        from fred_db import connect
        conn = connect()

        # Notizen
        count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        if count > 0:
            stats.append(f"📝 {count} Notizen")

        # Projekte
        count = conn.execute("SELECT COUNT(*) FROM projects WHERE status='active'").fetchone()[0]
        if count > 0:
            stats.append(f"📁 {count} aktive Projekte")

        # Tasks offen
        count = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='todo'").fetchone()[0]
        if count > 0:
            stats.append(f"📋 {count} offene Tasks")

        # Chat History
        count = conn.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
        if count > 0:
            stats.append(f"💬 {count} Nachrichten")

        # Code Snippets
        count = conn.execute("SELECT COUNT(*) FROM code_snippets").fetchone()[0]
        if count > 0:
            stats.append(f"💻 {count} Snippets")

        conn.close()
    except:
        pass

    if stats:
        print(f"\n  {DIM}{' │ '.join(stats)}{R}")


# ══════════════════════════════════════════
#  GRUSS
# ══════════════════════════════════════════

def greeting():
    hour = datetime.now().hour
    if hour < 6:
        return "🌙 Nachtschicht?"
    elif hour < 10:
        return "☀️ Guten Morgen!"
    elif hour < 13:
        return "👋 Mahlzeit bald!"
    elif hour < 17:
        return "🌤️ Guten Nachmittag!"
    elif hour < 21:
        return "🌆 Guten Abend!"
    else:
        return "🌙 Noch am Coden?"


# ══════════════════════════════════════════
#  HAUPTMENÜ
# ══════════════════════════════════════════

def main_menu():
    # Erst Datenbank initialisieren
    try:
        from fred_db import init_db
        init_db()
    except Exception as e:
        print(f"{RED}DB Fehler: {e}{R}")
        return

    while True:
        clear()
        show_banner()
        quick_stats()

        greet = greeting()

        print(f"""
  {greet}

  {CYAN}{BOLD}Was möchtest du tun?{R}

  {YELLOW}[1]{R} Chat           {DIM}Frag Fred alles{R}
  {YELLOW}[2]{R} Code Assistent {DIM}Generieren, erklaeren, debuggen{R}
  {YELLOW}[3]{R} Notizen        {DIM}Gedanken & Wissen speichern{R}
  {YELLOW}[4]{R} Projekte       {DIM}Tasks & Fortschritt tracken{R}
  {YELLOW}[5]{R} Tools          {DIM}System, Netzwerk, Backup...{R}
  {YELLOW}[6]{R} Einstellungen  {DIM}Provider, Modell, API Key{R}
  {YELLOW}[7]{R} Agent          {DIM}Fred macht es fuer dich{R}

  {YELLOW}[q]{R} Beenden
""")

        choice = input(f"  {CYAN}▸{R} ").strip().lower()

        if choice in ('1', 'chat', 'c'):
            try:
                from fred_chat import chat_menu
                chat_menu()
            except ImportError as e:
                module_error("fred_chat", e)

        elif choice in ('2', 'code', 'co'):
            try:
                from fred_coder import coder_menu
                coder_menu()
            except ImportError as e:
                module_error("fred_coder", e)

        elif choice in ('3', 'notes', 'n'):
            try:
                from fred_notes import notes_menu
                notes_menu()
            except ImportError as e:
                module_error("fred_notes", e)

        elif choice in ('4', 'projects', 'p'):
            try:
                from fred_projects import projects_menu
                projects_menu()
            except ImportError as e:
                module_error("fred_projects", e)

        elif choice in ('5', 'tools', 't'):
            try:
                from fred_tools import tools_menu
                tools_menu()
            except ImportError as e:
                module_error("fred_tools", e)

        elif choice in ('6', 'settings', 's'):
            try:
                from fred_settings import settings_menu
                settings_menu()
            except ImportError as e:
                module_error("fred_settings", e)

        elif choice in ('7', 'agent', 'a'):
            from fred_agent import agent_loop
            db_path = os.path.join(os.path.dirname(__file__), 'fred.db')
            agent_loop(db_path)

        elif choice in ('q', 'quit', 'exit', '0'):
            farewell()
            break

        # Easter Eggs & Quick Commands
        elif choice == 'fred':
            clear()
            print(f"\n  {CYAN}{BOLD}Ja? 😊{R}")
            time.sleep(1)

        elif choice == 'version':
            clear()
            print(f"\n  {CYAN}FRED v{VERSION}{R}")
            print(f"  {DIM}Terminal AI Assistent{R}")
            print(f"  {DIM}Made with ❤️ on Raspberry Pi{R}")
            input(f"\n  {DIM}Enter...{R}")

        elif choice == 'status':
            show_status()

        elif choice == 'backup':
            try:
                from fred_tools import backup_tool
                backup_tool()
            except:
                pass

        elif choice == '':
            continue

        else:
            print(f"\n  {DIM}Unbekannt: '{choice}' — Wähle 1-7 oder q{R}")
            time.sleep(1)


# ══════════════════════════════════════════
#  STATUS CHECK
# ══════════════════════════════════════════

def show_status():
    clear()
    width = os.get_terminal_size().columns
    print(f"\n{MAGENTA}{BOLD}{'═' * width}")
    print(f"  ⚙️  FRED Status Check")
    print(f"{'═' * width}{R}\n")

    modules = {
        'fred_db': '🗄️  Datenbank',
        'fred_cloud': '☁️  Cloud API',
        'fred_settings': '⚙️  Einstellungen',
        'fred_chat': '💬 Chat',
        'fred_coder': '💻 Code Assistent',
        'fred_notes': '📝 Notizen',
        'fred_projects': '📁 Projekte',
        'fred_tools': '🔧 Tools',
    }

    all_ok = True
    for mod, name in modules.items():
        try:
            __import__(mod)
            print(f"  {GREEN}✅{R} {name} ({mod}.py)")
        except ImportError as e:
            print(f"  {RED}❌{R} {name} ({mod}.py) — {e}")
            all_ok = False

    # DB Check
    print(f"\n  {BOLD}Datenbank:{R}")
    try:
        from fred_db import connect
        conn = connect()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        for t in tables:
            print(f"    {GREEN}✓{R} {t['name']}")
    except Exception as e:
        print(f"    {RED}✗ {e}{R}")

    # Provider Check
    print(f"\n  {BOLD}AI Provider:{R}")
    try:
        from fred_settings import get_provider, get_model, get_api_key, PROVIDERS
        provider = get_provider()
        info = PROVIDERS.get(provider, dict())
        print(f"    Provider: {info.get('name', provider)}")
        print(f"    Modell:   {get_model()}")
        key = get_api_key()
        if provider == "ollama_local":
            print(f"    Auth:     {GREEN}Nicht nötig (lokal){R}")
        elif key:
            print(f"    API Key:  {GREEN}✅ Gesetzt (...{key[-6:]}){R}")
        else:
            print(f"    API Key:  {RED}❌ Nicht gesetzt{R}")
    except:
        print(f"    {RED}Nicht konfiguriert{R}")

    # Disk
    import shutil
    stat = shutil.disk_usage(os.path.expanduser('~/fred'))
    free = stat.free / (1024**3)
    print(f"\n  {BOLD}System:{R}")
    print(f"    Disk frei: {free:.1f}GB")
    print(f"    Python:    {sys.version.split()[0]}")
    print(f"    Fred:      ~/fred/")

    if all_ok:
        print(f"\n  {GREEN}{BOLD}✅ Alle Module OK!{R}")
    else:
        print(f"\n  {RED}{BOLD}⚠️  Einige Module fehlen!{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  FEHLER HANDLER
# ══════════════════════════════════════════

def module_error(module, error):
    clear()
    print(f"\n  {RED}{BOLD}❌ Modul-Fehler{R}")
    print(f"  {RED}{module}.py konnte nicht geladen werden.{R}")
    print(f"  {DIM}{error}{R}")
    print(f"\n  {YELLOW}Lösung:{R}")
    print(f"  1. Prüfe ob {module}.py in ~/fred/ existiert")
    print(f"  2. Starte 'status' im Hauptmenü")
    print(f"  3. Erstelle die fehlende Datei neu")
    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  VERABSCHIEDUNG
# ══════════════════════════════════════════

def farewell():
    clear()
    hour = datetime.now().hour
    if hour < 12:
        msg = "Einen produktiven Tag! 🚀"
    elif hour < 18:
        msg = "Bis später! 👋"
    elif hour < 22:
        msg = "Schönen Feierabend! 🌙"
    else:
        msg = "Gute Nacht! 💤"

    box_top = "    ╔" + "═" * 34 + "╗"
    box_bot = "    ╚" + "═" * 34 + "╝"
    print(f"\n{CYAN}{BOLD}")
    print(box_top)
    print(f"    ║  Bis bald!                       ║")
    print(f"    ║  {msg:<33}║")
    print(f"    ║                                  ║")
    print(f"    ║  {DIM}Fred v{VERSION} • Made with ❤️{R}{CYAN}{BOLD}        ║")
    print(box_bot)
    print(f"{R}")


# ══════════════════════════════════════════
#  START
# ══════════════════════════════════════════

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        farewell()
    except Exception as e:
        print(f"\n{RED}Unerwarteter Fehler: {e}{R}")
        import traceback
        traceback.print_exc()
        print(f"\n{YELLOW}Versuche: cd ~/fred && python3 fred.py{R}")
