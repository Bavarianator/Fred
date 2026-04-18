"""
FRED v2.0 - Notizen System
Erstellen, suchen, taggen, AI-Zusammenfassungen
"""

import os
from datetime import datetime
from fred_db import connect
from fred_cloud import chat


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


def header(title="Notizen"):
    width = os.get_terminal_size().columns
    print(f"\n{BLUE}{BOLD}{'═' * width}")
    print(f"  📝 {title}")
    print(f"{'═' * width}{R}")


# ══════════════════════════════════════════
#  DATENBANK FUNKTIONEN
# ══════════════════════════════════════════

def create_note(title, content, category="allgemein", tags=""):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO notes (title, content, category, tags) VALUES (?,?,?,?)",
        (title, content, category, tags)
    )
    conn.commit()
    nid = c.lastrowid
    conn.close()
    return nid


def get_notes(search=None, category=None, tag=None):
    conn = connect()
    if search:
        rows = conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY pinned DESC, updated_at DESC",
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    elif category:
        rows = conn.execute(
            "SELECT * FROM notes WHERE category=? ORDER BY pinned DESC, updated_at DESC",
            (category,)
        ).fetchall()
    elif tag:
        rows = conn.execute(
            "SELECT * FROM notes WHERE tags LIKE ? ORDER BY pinned DESC, updated_at DESC",
            (f"%{tag}%",)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM notes ORDER BY pinned DESC, updated_at DESC"
        ).fetchall()
    conn.close()
    return rows


def get_note(note_id):
    conn = connect()
    row = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    conn.close()
    return row


def update_note(note_id, **kwargs):
    conn = connect()
    note = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not note:
        conn.close()
        return False

    title = kwargs.get('title', note['title'])
    content = kwargs.get('content', note['content'])
    category = kwargs.get('category', note['category'])
    tags = kwargs.get('tags', note['tags'])
    pinned = kwargs.get('pinned', note['pinned'])

    conn.execute(
        "UPDATE notes SET title=?, content=?, category=?, tags=?, pinned=?, updated_at=? WHERE id=?",
        (title, content, category, tags, pinned, datetime.now().isoformat(), note_id)
    )
    conn.commit()
    conn.close()
    return True


def delete_note(note_id):
    conn = connect()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()


def get_categories():
    conn = connect()
    rows = conn.execute(
        "SELECT DISTINCT category FROM notes WHERE category != '' ORDER BY category"
    ).fetchall()
    conn.close()
    return [r['category'] for r in rows]


def get_all_tags():
    conn = connect()
    rows = conn.execute("SELECT tags FROM notes WHERE tags != ''").fetchall()
    conn.close()
    all_tags = set()
    for r in rows:
        for t in r['tags'].split(','):
            t = t.strip()
            if t:
                all_tags.add(t)
    return sorted(all_tags)


# ══════════════════════════════════════════
#  NOTIZ ANZEIGEN
# ══════════════════════════════════════════

def note_view(note_id):
    """Einzelne Notiz anzeigen mit Optionen"""
    while True:
        clear()
        note = get_note(note_id)
        if not note:
            print(f"  {RED}Notiz nicht gefunden.{R}")
            input(f"\n  {DIM}Enter...{R}")
            return

        header(note['title'])

        pin = "📌 " if note['pinned'] else ""
        cat = note['category'] or "allgemein"
        tags = note['tags'] or "-"
        date = note['updated_at'][:16] if note['updated_at'] else note['created_at'][:16]

        print(f"  {pin}{DIM}Kategorie: {cat} | Tags: {tags} | {date}{R}")
        print(f"  {'─' * 50}")
        print()

        # Inhalt anzeigen
        for line in note['content'].split('\n'):
            print(f"  {line}")

        print(f"\n  {'─' * 50}")
        print(f"  {YELLOW}[e]{R} Bearbeiten    {YELLOW}[t]{R} Tags ändern")
        print(f"  {YELLOW}[k]{R} Kategorie     {YELLOW}[p]{R} Pin {'entfernen' if note['pinned'] else 'setzen'}")
        print(f"  {YELLOW}[a]{R} AI Zusammenfassung")
        print(f"  {YELLOW}[v]{R} AI Verbessern")
        print(f"  {RED}[x]{R} Löschen       {DIM}[Enter] Zurück{R}")

        choice = input(f"\n  {CYAN}▸{R} ").strip().lower()

        if choice == '':
            return
        elif choice == 'e':
            note_edit(note_id)
        elif choice == 't':
            new_tags = input(f"  Tags (komma-getrennt): {CYAN}▸{R} ").strip()
            update_note(note_id, tags=new_tags)
            print(f"  {GREEN}✅ Tags aktualisiert{R}")
        elif choice == 'k':
            new_cat = input(f"  Kategorie: {CYAN}▸{R} ").strip()
            if new_cat:
                update_note(note_id, category=new_cat)
                print(f"  {GREEN}✅ Kategorie geändert{R}")
        elif choice == 'p':
            new_pin = 0 if note['pinned'] else 1
            update_note(note_id, pinned=new_pin)
        elif choice == 'a':
            ai_summarize(note)
        elif choice == 'v':
            ai_improve(note)
        elif choice == 'x':
            print(f"\n  {RED}Wirklich löschen? (j/n){R}")
            if input(f"  {CYAN}▸{R} ").strip().lower() == 'j':
                delete_note(note_id)
                print(f"  {GREEN}✅ Gelöscht{R}")
                input(f"\n  {DIM}Enter...{R}")
                return


def note_edit(note_id):
    """Notiz bearbeiten"""
    note = get_note(note_id)
    if not note:
        return

    print(f"\n  {DIM}Aktueller Titel: {note['title']}{R}")
    new_title = input(f"  Neuer Titel (Enter=behalten): {CYAN}▸{R} ").strip()

    print(f"\n  {DIM}Neuen Inhalt eingeben (leere Zeile + 'ENDE' zum Speichern):{R}")
    print(f"  {DIM}(Enter für alten Inhalt behalten){R}")

    first = input(f"  {CYAN}▸{R} ")
    if first == '':
        # Nur Titel ändern
        if new_title:
            update_note(note_id, title=new_title)
            print(f"  {GREEN}✅ Titel aktualisiert{R}")
        return

    lines = [first]
    while True:
        line = input(f"  {CYAN}▸{R} ")
        if line.strip().upper() == 'ENDE':
            break
        lines.append(line)

    content = '\n'.join(lines)
    update_note(
        note_id,
        title=new_title if new_title else note['title'],
        content=content
    )
    print(f"  {GREEN}✅ Notiz aktualisiert!{R}")
    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  AI FUNKTIONEN
# ══════════════════════════════════════════

def ai_summarize(note):
    """Einzelne Notiz zusammenfassen"""
    print(f"\n  {YELLOW}⏳ Erstelle Zusammenfassung...{R}\n")

    system = "Fasse den folgenden Text kurz und prägnant zusammen. Nutze Bullet Points. Antworte auf Deutsch."
    messages = [{"role": "user", "content": f"Fasse zusammen:\n\n{note['content']}"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(f"  {GREEN}{'─' * 50}{R}")
        print(f"  {BOLD}📋 Zusammenfassung: {note['title']}{R}\n")
        print(result)
        print(f"\n  {GREEN}{'─' * 50}{R}")
    else:
        print(f"  {RED}❌ {result}{R}")

    input(f"\n  {DIM}Enter...{R}")


def ai_improve(note):
    """AI verbessert Notiz"""
    print(f"\n  {YELLOW}⏳ Verbessere Notiz...{R}\n")

    system = """Verbessere den folgenden Text:
- Korrigiere Rechtschreibung und Grammatik
- Verbessere Struktur und Klarheit
- Behalte den Inhalt bei
Antworte auf Deutsch."""

    messages = [{"role": "user", "content": f"Verbessere:\n\n{note['content']}"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(f"  {GREEN}{'─' * 50}{R}")
        print(result)
        print(f"\n  {GREEN}{'─' * 50}{R}")
        print(f"\n  {YELLOW}[j]{R} Übernehmen  {DIM}[Enter] Verwerfen{R}")

        if input(f"  {CYAN}▸{R} ").strip().lower() == 'j':
            update_note(note['id'], content=result)
            print(f"  {GREEN}✅ Notiz aktualisiert!{R}")
            input(f"\n  {DIM}Enter...{R}")
    else:
        print(f"  {RED}❌ {result}{R}")
        input(f"\n  {DIM}Enter...{R}")


def ai_summary_all():
    """Alle Notizen zusammenfassen"""
    notes = get_notes()
    if not notes:
        print(f"\n  {DIM}Keine Notizen vorhanden.{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    print(f"\n  {YELLOW}⏳ Fasse {len(notes)} Notizen zusammen...{R}\n")

    all_text = ""
    for n in notes:
        all_text += f"### {n['title']} ({n['category']})\n{n['content']}\n\n"

    system = "Erstelle eine strukturierte Übersicht aller Notizen. Gruppiere nach Themen. Antworte auf Deutsch."
    messages = [{"role": "user", "content": f"Übersicht aller Notizen:\n\n{all_text}"}]
    result = chat(messages, system=system)

    if result and not result.startswith("Fehler:"):
        print(f"  {GREEN}{'─' * 50}{R}")
        print(f"  {BOLD}📋 Gesamt-Übersicht{R}\n")
        print(result)
        print(f"\n  {GREEN}{'─' * 50}{R}")
    else:
        print(f"  {RED}❌ {result}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  HAUPTMENÜ NOTIZEN
# ══════════════════════════════════════════

def notes_menu():
    """Notizen Hauptmenü"""
    while True:
        clear()
        header("Notizen")

        notes = get_notes()

        options = [
            ("1", "➕ Neue Notiz",          "Notiz erstellen"),
            ("2", "📋 Alle Notizen",        f"{len(notes)} Notizen"),
            ("3", "🔍 Suchen",              "Volltextsuche"),
            ("4", "📁 Kategorien",          "Nach Kategorie filtern"),
            ("5", "🏷  Tags",               "Nach Tags filtern"),
            ("6", "🤖 AI Zusammenfassung",  "Alle Notizen zusammenfassen"),
            ("0", "↩  Zurück",             "Zum Hauptmenü"),
        ]

        for key, title, desc in options:
            print(f"  {YELLOW}[{key}]{R} {title}  {DIM}{desc}{R}")

        choice = input(f"\n  {CYAN}▸{R} ").strip()

        if choice == '0':
            return
        elif choice == '1':
            note_create()
        elif choice == '2':
            note_list()
        elif choice == '3':
            note_search()
        elif choice == '4':
            note_categories()
        elif choice == '5':
            note_tags()
        elif choice == '6':
            ai_summary_all()


# ══════════════════════════════════════════
#  NEUE NOTIZ
# ══════════════════════════════════════════

def note_create():
    """Neue Notiz erstellen"""
    clear()
    header("Neue Notiz")

    title = input(f"  Titel: {CYAN}▸{R} ").strip()
    if not title:
        return

    cats = get_categories()
    if cats:
        print(f"\n  {DIM}Vorhandene: {', '.join(cats)}{R}")
    category = input(f"  Kategorie: {CYAN}▸{R} ").strip() or "allgemein"

    tags = input(f"  Tags (komma-getrennt): {CYAN}▸{R} ").strip()

    print(f"\n  {DIM}Inhalt eingeben (leere Zeile + 'ENDE' zum Speichern):{R}")
    lines = []
    while True:
        line = input(f"  {CYAN}▸{R} ")
        if line.strip().upper() == 'ENDE':
            break
        lines.append(line)

    content = '\n'.join(lines)
    if not content:
        print(f"  {RED}Kein Inhalt - abgebrochen.{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    nid = create_note(title, content, category, tags)
    print(f"\n  {GREEN}✅ Notiz #{nid} erstellt!{R}")
    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  LISTEN & FILTER
# ══════════════════════════════════════════

def note_list(notes=None, title_text="Alle Notizen"):
    """Notizen auflisten und auswählen"""
    if notes is None:
        notes = get_notes()

    if not notes:
        print(f"\n  {DIM}Keine Notizen vorhanden.{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    clear()
    header(title_text)

    for i, n in enumerate(notes, 1):
        pin = "📌" if n['pinned'] else "  "
        cat = n['category'] or ""
        date = n['updated_at'][:10] if n['updated_at'] else ""
        preview = n['content'][:60].replace('\n', ' ')
        print(f"  {pin} {YELLOW}[{i}]{R} {BOLD}{n['title']}{R}")
        print(f"       {DIM}{cat} | {date} | {preview}...{R}")

    print(f"\n  {DIM}Nummer zum Öffnen, Enter=zurück{R}")
    choice = input(f"  {CYAN}▸{R} ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(notes):
            note_view(notes[idx]['id'])
            note_list(notes, title_text)


def note_search():
    """Notizen durchsuchen"""
    clear()
    header("Suche")

    query = input(f"  Suchbegriff: {CYAN}▸{R} ").strip()
    if not query:
        return

    results = get_notes(search=query)
    print(f"\n  {GREEN}{len(results)} Treffer für '{query}'{R}")

    if results:
        note_list(results, f"Suche: {query}")


def note_categories():
    """Nach Kategorie filtern"""
    clear()
    header("Kategorien")

    cats = get_categories()
    if not cats:
        print(f"\n  {DIM}Keine Kategorien vorhanden.{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    for i, c in enumerate(cats, 1):
        count = len(get_notes(category=c))
        print(f"  {YELLOW}[{i}]{R} {c} {DIM}({count}){R}")

    choice = input(f"\n  {CYAN}▸{R} ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(cats):
            results = get_notes(category=cats[idx])
            note_list(results, f"Kategorie: {cats[idx]}")


def note_tags():
    """Nach Tags filtern"""
    clear()
    header("Tags")

    tags = get_all_tags()
    if not tags:
        print(f"\n  {DIM}Keine Tags vorhanden.{R}")
        input(f"\n  {DIM}Enter...{R}")
        return

    for i, t in enumerate(tags, 1):
        count = len(get_notes(tag=t))
        print(f"  {YELLOW}[{i}]{R} 🏷  {t} {DIM}({count}){R}")

    choice = input(f"\n  {CYAN}▸{R} ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(tags):
            results = get_notes(tag=tags[idx])
            note_list(results, f"Tag: {tags[idx]}")


# ══════════════════════════════════════════
#  SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    from fred_db import init_db
    init_db()

    print(f"{BLUE}{BOLD}📝 Fred Notizen System{R}")
    print(f"{'=' * 40}")

    notes = get_notes()
    cats = get_categories()
    tags = get_all_tags()

    print(f"\n  📝 {len(notes)} Notizen")
    print(f"  📁 {len(cats)} Kategorien")
    print(f"  🏷  {len(tags)} Tags")

    print(f"\n  Funktionen:")
    print(f"    ➕ Erstellen, bearbeiten, löschen")
    print(f"    🔍 Volltextsuche")
    print(f"    📁 Kategorien & Tags")
    print(f"    📌 Pinnen")
    print(f"    🤖 AI Zusammenfassung & Verbesserung")

    print(f"\n  ✅ fred_notes.py geladen!")
