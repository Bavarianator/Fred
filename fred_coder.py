"""
FRED v2.0 - Code Werkstatt
Code generieren, erklären, debuggen, Snippets verwalten
"""

import os
import sys
from datetime import datetime
from fred_db import (
    create_snippet, get_snippets, get_snippet, delete_snippet,
    get_setting
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


def clear():
    os.system('clear')


def header(title="Code Werkstatt"):
    width = os.get_terminal_size().columns
    print(f"\n{MAGENTA}{BOLD}{'═' * width}")
    print(f"  💻 {title}")
    print(f"{'═' * width}{R}")


# ══════════════════════════════════════════
#  CODE WERKSTATT MENÜ
# ══════════════════════════════════════════

def coder_menu():
    """Hauptmenü Code Werkstatt"""
    while True:
        clear()
        header("Code Werkstatt")

        options = [
            ("1", "🔨 Code generieren",    "AI schreibt Code für dich"),
            ("2", "🔍 Code erklären",       "Paste Code → AI erklärt"),
            ("3", "🐛 Code debuggen",       "Fehler finden und fixen"),
            ("4", "🔄 Code umwandeln",      "Sprache A → Sprache B"),
            ("5", "📚 Snippet Bibliothek",  "Gespeicherte Code-Schnipsel"),
            ("6", "📝 Datei analysieren",   "AI analysiert eine Datei"),
            ("0", "↩  Zurück",             "Zum Hauptmenü"),
        ]

        for key, title, desc in options:
            print(f"  {YELLOW}[{key}]{R} {title}")
            print(f"      {DIM}{desc}{R}")

        print()
        choice = input(f"  {CYAN}▸{R} ").strip()

        if choice == "1":
            code_generate()
        elif choice == "2":
            code_explain()
        elif choice == "3":
            code_debug()
        elif choice == "4":
            code_convert()
        elif choice == "5":
            snippet_menu()
        elif choice == "6":
            file_analyze()
        elif choice == "0":
            break


# ══════════════════════════════════════════
#  CODE GENERIEREN
# ══════════════════════════════════════════

def code_generate():
    """AI generiert Code nach Beschreibung"""
    clear()
    header("Code generieren")

    # Sprache wählen
    languages = ["Python", "Bash", "JavaScript", "HTML/CSS", "SQL", "C/C++", "Andere"]
    print(f"\n  {BOLD}Sprache wählen:{R}")
    for i, lang in enumerate(languages, 1):
        print(f"    {YELLOW}[{i}]{R} {lang}")

    print()
    lang_choice = input(f"  {CYAN}▸{R} ").strip()

    if lang_choice.isdigit() and 1 <= int(lang_choice) <= len(languages):
        language = languages[int(lang_choice) - 1]
        if language == "Andere":
            language = input(f"  Welche Sprache? {CYAN}▸{R} ").strip()
    else:
        language = "Python"

    # Beschreibung
    print(f"\n  {BOLD}Was soll der Code tun?{R}")
    print(f"  {DIM}(Beschreibe so genau wie möglich){R}")
    print()
    desc = input(f"  {CYAN}▸{R} ").strip()

    if not desc:
        return

    # An AI senden
    print(f"\n  {YELLOW}⏳ Generiere {language} Code...{R}\n")

    system = f"""Du bist ein erfahrener {language}-Programmierer.
Generiere sauberen, kommentierten Code.
Antworte NUR mit dem Code und einer kurzen Erklärung danach.
Nutze Best Practices. Antworte auf Deutsch."""

    messages = [{"role": "user", "content": f"Schreibe {language} Code: {desc}"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        content = result
        print(f"  {GREEN}{'─' * 50}{R}")
        print(content)
        print(f"  {GREEN}{'─' * 50}{R}")

        # Speichern anbieten
        print(f"\n  {YELLOW}[s]{R} Als Snippet speichern")
        print(f"  {YELLOW}[c]{R} In Datei speichern")
        print(f"  {DIM}[Enter] Weiter{R}")

        action = input(f"\n  {CYAN}▸{R} ").strip().lower()

        if action == "s":
            title = input(f"  Snippet-Name: {CYAN}▸{R} ").strip()
            if title:
                create_snippet(title, content, language.lower(), desc)
                print(f"  {GREEN}✅ Snippet gespeichert!{R}")
                input(f"\n  {DIM}Enter...{R}")

        elif action == "c":
            filename = input(f"  Dateiname: {CYAN}▸{R} ").strip()
            if filename:
                filepath = os.path.expanduser(f"~/{filename}")
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  {GREEN}✅ Gespeichert: {filepath}{R}")
                input(f"\n  {DIM}Enter...{R}")
    else:
        print(f"  {RED}❌ Fehler: {result}{R}")
        input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  CODE ERKLÄREN
# ══════════════════════════════════════════

def code_explain():
    """AI erklärt eingefügten Code"""
    clear()
    header("Code erklären")

    print(f"  {BOLD}Füge deinen Code ein:{R}")
    print(f"  {DIM}(Leere Zeile + Enter zum Beenden){R}\n")

    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
            lines.append(line)
        else:
            lines.append(line)

    code = "\n".join(lines).strip()
    if not code:
        return

    print(f"\n  {YELLOW}⏳ Analysiere Code...{R}\n")

    system = """Du bist ein Code-Erklärer. Erkläre den Code Zeile für Zeile.
Nutze einfache Sprache. Nenne auch mögliche Verbesserungen.
Antworte auf Deutsch."""

    messages = [{"role": "user", "content": f"Erkläre diesen Code:\n\n```\n{code}\n```"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(f"  {GREEN}{'─' * 50}{R}")
        print(result)
        print(f"  {GREEN}{'─' * 50}{R}")
    else:
        print(f"  {RED}❌ Fehler: {result}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  CODE DEBUGGEN
# ══════════════════════════════════════════

def code_debug():
    """AI findet und fixt Bugs"""
    clear()
    header("Code debuggen")

    print(f"  {BOLD}Füge den fehlerhaften Code ein:{R}")
    print(f"  {DIM}(Leere Zeile + Enter zum Beenden){R}\n")

    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
            lines.append(line)
        else:
            lines.append(line)

    code = "\n".join(lines).strip()
    if not code:
        return

    # Optionale Fehlermeldung
    print(f"\n  {BOLD}Fehlermeldung (optional, Enter zum Überspringen):{R}")
    error_msg = input(f"  {CYAN}▸{R} ").strip()

    print(f"\n  {YELLOW}⏳ Suche Fehler...{R}\n")

    system = """Du bist ein Code-Debugger. Finde alle Fehler im Code.
Für jeden Fehler:
1. Was ist falsch
2. Warum es falsch ist
3. Der Fix

Zeige am Ende den korrigierten vollständigen Code.
Antworte auf Deutsch."""

    prompt = f"Debugge diesen Code:\n\n```\n{code}\n```"
    if error_msg:
        prompt += f"\n\nFehlermeldung: {error_msg}"

    messages = [{"role": "user", "content": prompt}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(f"  {GREEN}{'─' * 50}{R}")
        print(result)
        print(f"  {GREEN}{'─' * 50}{R}")
    else:
        print(f"  {RED}❌ Fehler: {result}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  CODE UMWANDELN
# ══════════════════════════════════════════

def code_convert():
    """Wandelt Code von Sprache A nach B um"""
    clear()
    header("Code umwandeln")

    languages = ["Python", "Bash", "JavaScript", "TypeScript", "Go", "Rust", "C", "Java", "PHP"]

    print(f"  {BOLD}VON welcher Sprache?{R}")
    for i, lang in enumerate(languages, 1):
        print(f"    {YELLOW}[{i}]{R} {lang}")

    from_choice = input(f"\n  {CYAN}▸{R} ").strip()
    from_lang = languages[int(from_choice) - 1] if from_choice.isdigit() and 1 <= int(from_choice) <= len(languages) else "Python"

    print(f"\n  {BOLD}NACH welcher Sprache?{R}")
    for i, lang in enumerate(languages, 1):
        print(f"    {YELLOW}[{i}]{R} {lang}")

    to_choice = input(f"\n  {CYAN}▸{R} ").strip()
    to_lang = languages[int(to_choice) - 1] if to_choice.isdigit() and 1 <= int(to_choice) <= len(languages) else "Bash"

    print(f"\n  {BOLD}Füge den {from_lang}-Code ein:{R}")
    print(f"  {DIM}(Leere Zeile + Enter zum Beenden){R}\n")

    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
            lines.append(line)
        else:
            lines.append(line)

    code = "\n".join(lines).strip()
    if not code:
        return

    print(f"\n  {YELLOW}⏳ Wandle {from_lang} → {to_lang}...{R}\n")

    system = f"""Du bist ein Code-Konverter. Wandle Code von {from_lang} nach {to_lang} um.
Nutze die Best Practices und Idiome der Zielsprache.
Behalte die gleiche Funktionalität. Kommentiere auf Deutsch."""

    messages = [{"role": "user", "content": f"Wandle von {from_lang} nach {to_lang}:\n\n```{from_lang.lower()}\n{code}\n```"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(f"  {GREEN}{'─' * 50}{R}")
        print(result)
        print(f"  {GREEN}{'─' * 50}{R}")

        # Speichern
        print(f"\n  {YELLOW}[s]{R} Als Snippet speichern")
        print(f"  {DIM}[Enter] Weiter{R}")
        if input(f"\n  {CYAN}▸{R} ").strip().lower() == "s":
            title = input(f"  Name: {CYAN}▸{R} ").strip()
            if title:
                create_snippet(title, result, to_lang.lower(), f"Konvertiert von {from_lang}")
                print(f"  {GREEN}✅ Gespeichert!{R}")
                input(f"\n  {DIM}Enter...{R}")
    else:
        print(f"  {RED}❌ Fehler: {result}{R}")
        input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  DATEI ANALYSIEREN
# ══════════════════════════════════════════

def file_analyze():
    """Liest eine Datei und lässt AI sie analysieren"""
    clear()
    header("Datei analysieren")

    print(f"  {BOLD}Dateipfad eingeben:{R}")
    print(f"  {DIM}(z.B. ~/scripts/test.py){R}")
    filepath = input(f"\n  {CYAN}▸{R} ").strip()

    filepath = os.path.expanduser(filepath)

    if not os.path.isfile(filepath):
        print(f"  {RED}❌ Datei nicht gefunden: {filepath}{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    # Dateigröße prüfen
    size = os.path.getsize(filepath)
    if size > 50000:
        print(f"  {RED}❌ Datei zu groß ({size} Bytes). Max 50KB.{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"  {RED}❌ Lesefehler: {e}{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1]

    print(f"\n  📄 {filename} ({size} Bytes)")
    print(f"\n  {BOLD}Was möchtest du?{R}")
    print(f"    {YELLOW}[1]{R} Vollständige Analyse")
    print(f"    {YELLOW}[2]{R} Verbesserungen vorschlagen")
    print(f"    {YELLOW}[3]{R} Sicherheitsprüfung")
    print(f"    {YELLOW}[4]{R} Dokumentation generieren")

    action = input(f"\n  {CYAN}▸{R} ").strip()

    prompts = {
        "1": "Analysiere diese Datei vollständig. Erkläre was sie tut, wie sie strukturiert ist, und bewerte die Codequalität.",
        "2": "Finde Verbesserungsmöglichkeiten. Performance, Lesbarkeit, Best Practices.",
        "3": "Prüfe auf Sicherheitslücken und potenzielle Probleme.",
        "4": "Generiere eine vollständige Dokumentation (Docstrings, README-Style).",
    }

    prompt = prompts.get(action, prompts["1"])
    print(f"\n  {YELLOW}⏳ Analysiere {filename}...{R}\n")

    system = """Du bist ein erfahrener Code-Reviewer und Analyst.
Sei gründlich aber verständlich. Antworte auf Deutsch."""

    messages = [{"role": "user", "content": f"{prompt}\n\nDatei: {filename}\n\n```{ext}\n{content}\n```"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(f"  {GREEN}{'─' * 50}{R}")
        print(result)
        print(f"  {GREEN}{'─' * 50}{R}")
    else:
        print(f"  {RED}❌ Fehler: {result}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  SNIPPET BIBLIOTHEK
# ══════════════════════════════════════════

def snippet_menu():
    """Snippet-Verwaltung"""
    while True:
        clear()
        header("Snippet Bibliothek")

        snippets = get_snippets()

        if snippets:
            for i, s in enumerate(snippets, 1):
                lang_icon = {"python": "🐍", "bash": "🐚", "javascript": "📜", "html": "🌐"}.get(s['language'], "📄")
                print(f"  {YELLOW}[{i}]{R} {lang_icon} {s['title']} {DIM}({s['language']}){R}")
        else:
            print(f"  {DIM}Keine Snippets gespeichert.{R}")

        print(f"\n  {YELLOW}[n]{R} Neues Snippet")
        print(f"  {YELLOW}[s]{R} Suchen")
        print(f"  {YELLOW}[0]{R} Zurück")

        choice = input(f"\n  {CYAN}▸{R} ").strip().lower()

        if choice == "0":
            break
        elif choice == "n":
            snippet_create()
        elif choice == "s":
            snippet_search()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(snippets):
                snippet_view(snippets[idx]['id'])


def snippet_create():
    """Neues Snippet erstellen"""
    clear()
    header("Neues Snippet")

    title = input(f"  Name: {CYAN}▸{R} ").strip()
    if not title:
        return

    language = input(f"  Sprache {DIM}(python){R}: {CYAN}▸{R} ").strip() or "python"
    desc = input(f"  Beschreibung: {CYAN}▸{R} ").strip()
    tags = input(f"  Tags {DIM}(kommagetrennt){R}: {CYAN}▸{R} ").strip()

    print(f"\n  {BOLD}Code eingeben:{R}")
    print(f"  {DIM}(Leere Zeile + Enter zum Beenden){R}\n")

    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
            lines.append(line)
        else:
            lines.append(line)

    code = "\n".join(lines).strip()
    if code:
        create_snippet(title, code, language, desc, tags)
        print(f"\n  {GREEN}✅ Snippet '{title}' gespeichert!{R}")
    else:
        print(f"  {RED}❌ Kein Code eingegeben.{R}")

    input(f"\n  {DIM}Enter...{R}")


def snippet_view(snippet_id):
    """Snippet anzeigen"""
    clear()
    s = get_snippet(snippet_id)
    if not s:
        return

    header(f"Snippet: {s['title']}")

    print(f"\n  {BOLD}Sprache:{R} {s['language']}")
    if s['description']:
        print(f"  {BOLD}Beschreibung:{R} {s['description']}")
    if s['tags']:
        print(f"  {BOLD}Tags:{R} {s['tags']}")
    print(f"  {BOLD}Erstellt:{R} {s['created_at']}")

    print(f"\n  {GREEN}{'─' * 50}{R}")
    print(s['code'])
    print(f"  {GREEN}{'─' * 50}{R}")

    print(f"\n  {YELLOW}[d]{R} Löschen")
    print(f"  {YELLOW}[c]{R} In Datei speichern")
    print(f"  {YELLOW}[e]{R} AI erklären lassen")
    print(f"  {DIM}[Enter] Zurück{R}")

    action = input(f"\n  {CYAN}▸{R} ").strip().lower()

    if action == "d":
        confirm = input(f"  {RED}Wirklich löschen? (j/n):{R} ").strip().lower()
        if confirm == "j":
            delete_snippet(snippet_id)
            print(f"  {GREEN}✅ Gelöscht!{R}")
            input(f"\n  {DIM}Enter...{R}")
    elif action == "c":
        filename = input(f"  Dateiname: {CYAN}▸{R} ").strip()
        if filename:
            filepath = os.path.expanduser(f"~/{filename}")
            with open(filepath, 'w') as f:
                f.write(s['code'])
            print(f"  {GREEN}✅ Gespeichert: {filepath}{R}")
            input(f"\n  {DIM}Enter...{R}")
    elif action == "e":
        code_explain_snippet(s['code'])


def snippet_search():
    """Snippets durchsuchen"""
    clear()
    header("Snippet suchen")

    query = input(f"  Suchbegriff: {CYAN}▸{R} ").strip()
    if not query:
        return

    results = get_snippets(search=query)

    if results:
        print(f"\n  {GREEN}{len(results)} Ergebnis(se):{R}\n")
        for s in results:
            print(f"  📄 {BOLD}{s['title']}{R} ({s['language']})")
            if s['description']:
                print(f"     {DIM}{s['description']}{R}")
    else:
        print(f"\n  {DIM}Nichts gefunden.{R}")

    input(f"\n  {DIM}Enter...{R}")


def code_explain_snippet(code):
    """Erklärt einen Snippet via AI"""
    print(f"\n  {YELLOW}⏳ Erkläre Code...{R}\n")

    system = "Erkläre diesen Code einfach und verständlich auf Deutsch."
    messages = [{"role": "user", "content": f"Erkläre:\n```\n{code}\n```"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(result)
    else:
        print(f"  {RED}❌ {result}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    from fred_db import init_db
    init_db()

    print(f"{MAGENTA}{BOLD}💻 Fred Code Werkstatt{R}")
    print(f"{'=' * 40}")
    print(f"\n  Funktionen:")
    print(f"    🔨 Code generieren")
    print(f"    🔍 Code erklären")
    print(f"    🐛 Code debuggen")
    print(f"    🔄 Code umwandeln")
    print(f"    📚 Snippet Bibliothek")
    print(f"    📝 Datei analysieren")

    snippets = get_snippets()
    print(f"\n  📚 {len(snippets)} Snippets gespeichert")

    print(f"\n  ✅ fred_coder.py geladen!")
