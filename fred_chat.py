"""
FRED v2.0 - Chat System
Multi-Chat, Modi, Verlauf, Streaming-Feel
"""

import os
import sys
from datetime import datetime
from fred_db import (
    create_chat, get_chats, get_chat, delete_chat,
    save_message, get_messages, update_chat_title,
    get_setting, set_setting
)
from fred_cloud import chat, get_provider_info


# ══════════════════════════════════════════
#  FARBEN
# ══════════════════════════════════════════

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
R = "\033[0m"


# ══════════════════════════════════════════
#  CHAT MODI
# ══════════════════════════════════════════

CHAT_MODES = {
    "normal": {
        "name": "💬 Normal",
        "system": "Du bist Fred, ein hilfreicher und freundlicher AI-Assistent. Antworte auf Deutsch. Sei präzise aber freundlich.",
        "temp": 0.7,
    },
    "code": {
        "name": "💻 Code",
        "system": "Du bist Fred im Code-Modus. Du bist ein erfahrener Programmierer. Gib klaren, kommentierten Code. Erkläre kurz was du tust. Antworte auf Deutsch.",
        "temp": 0.3,
    },
    "creative": {
        "name": "🎨 Kreativ",
        "system": "Du bist Fred im Kreativ-Modus. Sei kreativ, inspirierend und denke um die Ecke. Antworte auf Deutsch.",
        "temp": 0.9,
    },
    "research": {
        "name": "🔬 Research",
        "system": "Du bist Fred im Research-Modus. Analysiere gründlich, nenne Vor- und Nachteile, sei objektiv und detailliert. Antworte auf Deutsch.",
        "temp": 0.4,
    },
    "minimal": {
        "name": "⚡ Minimal",
        "system": "Antworte so kurz wie möglich. Nur das Wesentliche. Deutsch.",
        "temp": 0.3,
    },
}


def clear():
    os.system('clear')


def header(title="Fred Chat"):
    """Zeigt Chat-Header"""
    width = os.get_terminal_size().columns
    print(f"\n{CYAN}{BOLD}{'═' * width}")
    print(f"  💬 {title}")
    print(f"{'═' * width}{R}")


def status_bar(chat_title, mode, provider_name, model):
    """Zeigt Statusleiste"""
    width = os.get_terminal_size().columns
    left = f" 📝 {chat_title}  │  {CHAT_MODES[mode]['name']}"
    right = f"📡 {provider_name} / {model} "
    padding = width - len(left) - len(right) + 20  # +20 wegen ANSI codes
    if padding < 2:
        padding = 2
    print(f"{DIM}{BLUE}{'─' * width}{R}")
    print(f"{DIM}{left}{' ' * padding}{right}{R}")
    print(f"{DIM}{BLUE}{'─' * width}{R}")


# ══════════════════════════════════════════
#  CHAT MENÜ
# ══════════════════════════════════════════

def chat_menu():
    """Hauptmenü für Chats"""
    while True:
        clear()
        header("Fred Chat")

        provider = get_provider_info()
        if provider:
            print(f"  {DIM}📡 {provider['name']} / {provider['model']}{R}\n")
        else:
            print(f"  {RED}⚠ Kein Provider aktiv!{R}\n")

        print(f"  {YELLOW}[1]{R} 💬 Neuer Chat")
        print(f"  {YELLOW}[2]{R} 📋 Chat-Verlauf")
        print(f"  {YELLOW}[3]{R} ⚡ Schnelle Frage")
        print(f"  {YELLOW}[4]{R} 🎯 Chat-Modi")
        print(f"  {YELLOW}[0]{R} ← Zurück\n")

        choice = input(f"  {CYAN}▸{R} ").strip()

        if choice == "1":
            new_chat()
        elif choice == "2":
            chat_history()
        elif choice == "3":
            quick_question()
        elif choice == "4":
            show_modes()
        elif choice == "0":
            break


# ══════════════════════════════════════════
#  NEUER CHAT
# ══════════════════════════════════════════

def new_chat(mode="normal"):
    """Startet einen neuen Chat"""
    provider = get_provider_info()
    if not provider:
        print(f"\n  {RED}❌ Kein Provider aktiv! Gehe zu Einstellungen.{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    mode_info = CHAT_MODES.get(mode, CHAT_MODES["normal"])
    chat_id = create_chat(title="Neuer Chat", mode=mode)

    run_chat(chat_id, mode)


def run_chat(chat_id, mode="normal"):
    """Chat-Loop"""
    provider = get_provider_info()
    if not provider:
        print(f"\n  {RED}❌ Kein Provider aktiv!{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    mode_info = CHAT_MODES.get(mode, CHAT_MODES["normal"])
    chat_data = get_chat(chat_id)
    is_first_message = True

    while True:
        clear()

        # Header
        chat_data = get_chat(chat_id)
        title = chat_data['title'] if chat_data else "Chat"
        header(title)
        status_bar(title, mode, provider['name'], provider['model'])

        # Bisherige Nachrichten anzeigen
        messages = get_messages(chat_id)
        display_messages(messages)

        # Input
        print(f"\n  {DIM}Befehle: /quit /mode /title /clear /delete{R}")
        print()

        try:
            user_input = input(f"  {GREEN}{BOLD}Du ▸{R} ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        # ── Befehle ──
        if user_input.startswith("/"):
            cmd = user_input.lower().split()[0]

            if cmd == "/quit" or cmd == "/q":
                break

            elif cmd == "/mode":
                new_mode = select_mode()
                if new_mode:
                    mode = new_mode
                    mode_info = CHAT_MODES[mode]
                continue

            elif cmd == "/title":
                new_title = input(f"  {CYAN}Neuer Titel: {R}").strip()
                if new_title:
                    update_chat_title(chat_id, new_title)
                continue

            elif cmd == "/clear":
                # Chat leeren aber behalten
                from fred_db import connect
                conn = connect()
                conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
                conn.commit()
                conn.close()
                is_first_message = True
                continue

            elif cmd == "/delete":
                confirm = input(f"  {RED}Chat wirklich löschen? (j/n): {R}").strip()
                if confirm.lower() == 'j':
                    delete_chat(chat_id)
                    print(f"  {RED}🗑 Chat gelöscht.{R}")
                    input(f"\n  {DIM}Enter...{R}")
                    return
                continue

            elif cmd == "/help":
                show_chat_help()
                continue

            else:
                print(f"  {RED}Unbekannter Befehl. /help für Hilfe{R}")
                input(f"\n  {DIM}Enter...{R}")
                continue

        # ── Nachricht senden ──
        save_message(chat_id, "user", user_input)

        # Auto-Titel beim ersten Satz
        if is_first_message:
            auto_title = user_input[:50]
            if len(user_input) > 50:
                auto_title += "..."
            update_chat_title(chat_id, auto_title)
            is_first_message = False

        # Verlauf für API vorbereiten
        messages = get_messages(chat_id)
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg['role'],
                "content": msg['content'],
            })

        # Antwort holen
        print(f"\n  {DIM}⏳ Fred denkt nach...{R}", end="", flush=True)

        try:
            result = chat(
                api_messages,
                system=mode_info['system'],
            )

            # Cursor zurück und Zeile löschen
            print(f"\r{' ' * 40}\r", end="")

            if result:
                save_message(chat_id, "assistant", result)
            else:
                print(f"\n  {RED}❌ Keine Antwort erhalten{R}")
                input(f"\n  {DIM}Enter...{R}")
        except Exception as e:
            print(f"\r{' ' * 40}\r", end="")
            print(f"\n  {RED}❌ {e}{R}")
            input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  NACHRICHTEN ANZEIGEN
# ══════════════════════════════════════════

def display_messages(messages):
    """Zeigt Chat-Verlauf formatiert an"""
    if not messages:
        print(f"\n  {DIM}Noch keine Nachrichten. Schreib etwas!{R}")
        return

    # Nur letzte 20 Nachrichten anzeigen
    shown = messages[-20:]
    if len(messages) > 20:
        print(f"\n  {DIM}... {len(messages) - 20} ältere Nachrichten ...{R}")

    for msg in shown:
        role = msg['role']
        content = msg['content']

        if role == "user":
            print(f"\n  {GREEN}{BOLD}Du ▸{R} {content}")
        elif role == "assistant":
            print(f"\n  {CYAN}{BOLD}Fred ▸{R}")
            # Content mit Einrückung
            for line in content.split('\n'):
                print(f"    {line}")


# ══════════════════════════════════════════
#  CHAT VERLAUF
# ══════════════════════════════════════════

def chat_history():
    """Zeigt alle bisherigen Chats"""
    while True:
        clear()
        header("Chat-Verlauf")

        chats = get_chats()

        if not chats:
            print(f"\n  {DIM}Noch keine Chats vorhanden.{R}")
            input(f"\n  {DIM}Enter...{R}")
            return

        for i, c in enumerate(chats):
            mode_icon = CHAT_MODES.get(c['mode'], CHAT_MODES['normal'])['name'][:2]
            date = c['created_at'][:10] if c['created_at'] else ""
            print(f"  {YELLOW}[{i+1}]{R} {mode_icon} {c['title']}")
            print(f"      {DIM}{date} │ ID: {c['id']}{R}")

        print(f"\n  {YELLOW}[0]{R} ← Zurück")
        print(f"  {YELLOW}[d]{R} 🗑 Chat löschen\n")

        choice = input(f"  {CYAN}▸{R} ").strip()

        if choice == "0":
            break
        elif choice.lower() == "d":
            delete_chat_prompt(chats)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(chats):
                c = chats[idx]
                run_chat(c['id'], c['mode'] or 'normal')
            else:
                print(f"  {RED}Ungültige Auswahl.{R}")
                input(f"\n  {DIM}Enter...{R}")


def delete_chat_prompt(chats):
    """Chat zum Löschen auswählen"""
    num = input(f"  {RED}Welche Nummer löschen? {R}").strip()
    if num.isdigit():
        idx = int(num) - 1
        if 0 <= idx < len(chats):
            confirm = input(f"  {RED}'{chats[idx]['title']}' löschen? (j/n): {R}").strip()
            if confirm.lower() == 'j':
                delete_chat(chats[idx]['id'])
                print(f"  {RED}🗑 Gelöscht.{R}")
                input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  SCHNELLE FRAGE
# ══════════════════════════════════════════

def quick_question():
    """Eine Frage ohne Chat zu erstellen"""
    clear()
    header("Schnelle Frage")

    provider = get_provider_info()
    if not provider:
        print(f"\n  {RED}❌ Kein Provider aktiv!{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    print(f"  {DIM}Stelle eine einzelne Frage (ohne Chat-Verlauf){R}\n")

    question = input(f"  {GREEN}Frage ▸{R} ").strip()
    if not question:
        return

    print(f"\n  {DIM}⏳ Fred denkt nach...{R}", flush=True)

    from fred_cloud import quick_ask
    result = quick_ask(question)

    clear()
    header("Schnelle Frage")

    print(f"\n  {GREEN}Frage ▸{R} {question}")
    print(f"\n  {CYAN}{BOLD}Fred ▸{R}")

    if result['ok']:
        for line in result['content'].split('\n'):
            print(f"    {line}")

        tokens = result.get('tokens_out', 0)
        if tokens:
            print(f"\n  {DIM}[{tokens} tokens]{R}")
    else:
        print(f"    {RED}❌ {result['error']}{R}")

    # Fragen ob speichern
    print(f"\n  {DIM}[s] Speichern als Chat  [Enter] Fertig{R}")
    action = input(f"\n  {CYAN}▸{R} ").strip().lower()

    if action == 's' and result['ok']:
        title = question[:50]
        chat_id = create_chat(title=title, mode='normal')
        save_message(chat_id, "user", question)
        save_message(chat_id, "assistant", result['content'])
        print(f"  {GREEN}✅ Als Chat gespeichert!{R}")
        input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  MODUS WÄHLEN
# ══════════════════════════════════════════

def select_mode():
    """Modus auswählen"""
    clear()
    header("Chat-Modus")

    modes = list(CHAT_MODES.items())
    for i, (key, info) in enumerate(modes):
        print(f"  {YELLOW}[{i+1}]{R} {info['name']}")
        print(f"      {DIM}Temp: {info['temp']}{R}")

    print(f"\n  {YELLOW}[0]{R} ← Abbrechen\n")

    choice = input(f"  {CYAN}▸{R} ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(modes):
            selected = modes[idx][0]
            print(f"\n  {GREEN}✅ Modus: {CHAT_MODES[selected]['name']}{R}")
            input(f"\n  {DIM}Enter...{R}")
            return selected

    return None


def show_modes():
    """Zeigt alle Modi mit Beschreibung"""
    clear()
    header("Chat-Modi Übersicht")

    for key, info in CHAT_MODES.items():
        print(f"\n  {BOLD}{info['name']}{R}")
        print(f"  {DIM}System: {info['system'][:80]}...{R}")
        print(f"  {DIM}Temperatur: {info['temp']}{R}")

    input(f"\n  {DIM}Enter...{R}")


def show_chat_help():
    """Zeigt Chat-Befehle"""
    clear()
    header("Chat-Befehle")

    commands = [
        ("/quit, /q", "Chat verlassen"),
        ("/mode", "Modus wechseln"),
        ("/title", "Chat umbenennen"),
        ("/clear", "Nachrichten löschen"),
        ("/delete", "Chat komplett löschen"),
        ("/help", "Diese Hilfe"),
    ]

    for cmd, desc in commands:
        print(f"  {YELLOW}{cmd:15}{R} {desc}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    from fred_db import init_db
    init_db()

    print(f"{CYAN}{BOLD}💬 Fred Chat System{R}")
    print(f"{'=' * 40}")
    print(f"\n  Verfügbare Modi:")
    for key, info in CHAT_MODES.items():
        print(f"    {info['name']} (temp: {info['temp']})")

    provider = get_provider_info()
    if provider:
        print(f"\n  📡 Provider: {provider['name']}")
    else:
        print(f"\n  ⚠️  Kein Provider aktiv")

    print(f"\n  ✅ fred_chat.py geladen!")
