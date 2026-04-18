"""
FRED v2.0 - Projekt Manager
Projekte erstellen, Tasks verwalten, Fortschritt tracken
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


def header(title="Projekte"):
    width = os.get_terminal_size().columns
    print(f"\n{MAGENTA}{BOLD}{'═' * width}")
    print(f"  📁 {title}")
    print(f"{'═' * width}{R}")


# ══════════════════════════════════════════
#  DATENBANK FUNKTIONEN
# ══════════════════════════════════════════

def create_project(name, description="", language="python"):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO projects (name, description, language) VALUES (?,?,?)",
        (name, description, language)
    )
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid


def get_projects(status=None):
    conn = connect()
    if status:
        rows = conn.execute(
            "SELECT * FROM projects WHERE status=? ORDER BY updated_at DESC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY status ASC, updated_at DESC"
        ).fetchall()
    conn.close()
    return rows


def get_project(pid):
    conn = connect()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    conn.close()
    return row


def update_project(pid, **kwargs):
    conn = connect()
    for key, val in kwargs.items():
        conn.execute(f"UPDATE projects SET {key}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (val, pid))
    conn.commit()
    conn.close()


def delete_project(pid):
    conn = connect()
    conn.execute("DELETE FROM tasks WHERE project_id=?", (pid,))
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  TASK FUNKTIONEN
# ══════════════════════════════════════════

def create_task(project_id, title, description="", priority="medium"):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (project_id, title, description, priority) VALUES (?,?,?,?)",
        (project_id, title, description, priority)
    )
    conn.commit()
    tid = c.lastrowid
    conn.close()
    return tid


def get_tasks(project_id, status=None):
    conn = connect()
    if status:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE project_id=? AND status=? ORDER BY priority_order ASC, created_at ASC",
            (project_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM tasks WHERE project_id=?
               ORDER BY CASE status WHEN 'doing' THEN 0 WHEN 'todo' THEN 1 WHEN 'done' THEN 2 END,
               CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 END,
               created_at ASC""",
            (project_id,)
        ).fetchall()
    conn.close()
    return rows


def get_task(tid):
    conn = connect()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    conn.close()
    return row


def update_task(tid, **kwargs):
    conn = connect()
    for key, val in kwargs.items():
        conn.execute(f"UPDATE tasks SET {key}=? WHERE id=?", (val, tid))
    conn.commit()
    conn.close()


def delete_task(tid):
    conn = connect()
    conn.execute("DELETE FROM tasks WHERE id=?", (tid,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  FORTSCHRITT
# ══════════════════════════════════════════

def get_progress(project_id):
    tasks = get_tasks(project_id)
    if not tasks:
        return 0, 0, 0, 0
    total = len(tasks)
    done = sum(1 for t in tasks if t["status"] == "done")
    doing = sum(1 for t in tasks if t["status"] == "doing")
    todo = total - done - doing
    return total, done, doing, todo


def progress_bar(done, total, width=20):
    if total == 0:
        return f"{DIM}[{'─' * width}] 0%{R}"
    pct = done / total
    filled = int(width * pct)
    bar = f"{'█' * filled}{'░' * (width - filled)}"
    color = GREEN if pct >= 0.8 else YELLOW if pct >= 0.4 else RED
    return f"{color}[{bar}] {int(pct * 100)}%{R}"


# ══════════════════════════════════════════
#  ANZEIGE FUNKTIONEN
# ══════════════════════════════════════════

STATUS_EMOJI = {
    "active": "🟢",
    "paused": "⏸️",
    "completed": "✅",
    "archived": "📦"
}

PRIORITY_EMOJI = {
    "high": f"{RED}🔴{R}",
    "medium": f"{YELLOW}🟡{R}",
    "low": f"{GREEN}🟢{R}"
}

TASK_STATUS = {
    "todo": f"{RED}☐{R}",
    "doing": f"{YELLOW}⏳{R}",
    "done": f"{GREEN}☑{R}"
}


def show_project_list(projects):
    if not projects:
        print(f"\n  {DIM}Keine Projekte vorhanden.{R}")
        return

    for p in projects:
        pid = p["id"]
        name = p["name"]
        status = p["status"]
        lang = p["language"] or ""
        emoji = STATUS_EMOJI.get(status, "📁")
        total, done, doing, todo = get_progress(pid)
        bar = progress_bar(done, total, 15)

        print(f"  {YELLOW}[{pid}]{R} {emoji} {BOLD}{name}{R} {DIM}({lang}){R}")
        print(f"       {bar}  {DIM}{done}/{total} Tasks{R}")


def show_task_list(tasks):
    if not tasks:
        print(f"\n  {DIM}Keine Tasks vorhanden.{R}")
        return

    for t in tasks:
        tid = t["id"]
        title = t["title"]
        status = t["status"]
        priority = t["priority"]
        s_emoji = TASK_STATUS.get(status, "☐")
        p_emoji = PRIORITY_EMOJI.get(priority, "")

        strike = f"{DIM}" if status == "done" else ""
        end_strike = f"{R}" if status == "done" else ""

        print(f"  {YELLOW}[{tid}]{R} {s_emoji} {p_emoji} {strike}{title}{end_strike}")


# ══════════════════════════════════════════
#  PROJEKT ERSTELLEN
# ══════════════════════════════════════════

def new_project():
    clear()
    header("Neues Projekt")

    name = input(f"\n  {CYAN}Projekt Name:{R} ").strip()
    if not name:
        return

    desc = input(f"  {CYAN}Beschreibung:{R} ").strip()

    print(f"\n  {CYAN}Sprache:{R}")
    langs = ["python", "javascript", "bash", "html/css", "c/c++", "rust", "go", "andere"]
    for i, l in enumerate(langs, 1):
        print(f"    {YELLOW}[{i}]{R} {l}")

    lc = input(f"\n  {CYAN}Wahl (1):{R} ").strip()
    if lc.isdigit() and 1 <= int(lc) <= len(langs):
        lang = langs[int(lc) - 1]
    else:
        lang = "python"

    pid = create_project(name, desc, lang)
    print(f"\n  {GREEN}✅ Projekt '{name}' erstellt! (ID: {pid}){R}")

    # AI Tasks vorschlagen?
    ai = input(f"\n  {CYAN}Soll AI Tasks vorschlagen? (j/n):{R} ").strip().lower()
    if ai in ("j", "ja", "y"):
        suggest_tasks(pid, name, desc, lang)

    input(f"\n  {DIM}Enter...{R}")


def suggest_tasks(pid, name, desc, lang):
    print(f"\n  {CYAN}🤖 AI generiert Tasks...{R}")
    prompt = f"""Erstelle eine Liste von 5-8 Tasks für dieses Projekt:
Projekt: {name}
Beschreibung: {desc}
Sprache: {lang}

Antworte NUR mit einer nummerierten Liste, eine Task pro Zeile.
Format: Nummer. Task-Beschreibung
Keine weiteren Erklärungen."""

    result = chat(prompt, system="Du bist ein erfahrener Projektmanager und Entwickler.")

    if "❌" in result:
        print(f"  {RED}{result}{R}")
        return

    print(f"\n  {GREEN}Vorgeschlagene Tasks:{R}\n")
    lines = [l.strip() for l in result.strip().split('\n') if l.strip()]
    tasks = []
    for line in lines:
        # Nummer entfernen
        clean = line.lstrip('0123456789.-) ').strip()
        if clean:
            tasks.append(clean)
            print(f"    ✦ {clean}")

    add = input(f"\n  {CYAN}Alle hinzufügen? (j/n):{R} ").strip().lower()
    if add in ("j", "ja", "y"):
        for t in tasks:
            create_task(pid, t)
        print(f"  {GREEN}✅ {len(tasks)} Tasks hinzugefügt!{R}")


# ══════════════════════════════════════════
#  PROJEKT DETAIL
# ══════════════════════════════════════════

def project_detail(pid):
    while True:
        clear()
        project = get_project(pid)
        if not project:
            print(f"  {RED}Projekt nicht gefunden.{R}")
            input(f"  {DIM}Enter...{R}")
            return

        name = project["name"]
        desc = project["description"]
        status = project["status"]
        lang = project["language"]
        emoji = STATUS_EMOJI.get(status, "📁")
        total, done, doing, todo = get_progress(pid)

        header(f"{name}")
        print(f"""
  {emoji} Status: {status}  │  🔤 Sprache: {lang}
  {DIM}{desc}{R}

  {BOLD}Fortschritt:{R} {progress_bar(done, total, 25)}
  {DIM}✅ {done} erledigt  │  ⏳ {doing} in Arbeit  │  ☐ {todo} offen{R}
        """)

        tasks = get_tasks(pid)
        print(f"  {BOLD}Tasks:{R}")
        show_task_list(tasks)

        print(f"""
  {YELLOW}[a]{R} ➕ Task hinzufügen     {YELLOW}[t]{R} Task bearbeiten
  {YELLOW}[d]{R} Task erledigen          {YELLOW}[x]{R} Task löschen
  {YELLOW}[s]{R} Status ändern           {YELLOW}[e]{R} Projekt bearbeiten
  {YELLOW}[i]{R} 🤖 AI Tasks vorschlagen {YELLOW}[r]{R} 🤖 AI Review
  {YELLOW}[0]{R} Zurück
        """)

        choice = input(f"  {CYAN}▸{R} ").strip().lower()

        if choice == "a":
            add_task_interactive(pid)
        elif choice == "t":
            edit_task_interactive(pid)
        elif choice == "d":
            complete_task_interactive(pid)
        elif choice == "x":
            delete_task_interactive(pid)
        elif choice == "s":
            change_project_status(pid)
        elif choice == "e":
            edit_project(pid)
        elif choice == "i":
            p = get_project(pid)
            suggest_tasks(pid, p["name"], p["description"], p["language"])
            input(f"  {DIM}Enter...{R}")
        elif choice == "r":
            ai_project_review(pid)
        elif choice == "0":
            break


# ══════════════════════════════════════════
#  TASK INTERAKTIONEN
# ══════════════════════════════════════════

def add_task_interactive(pid):
    print()
    title = input(f"  {CYAN}Task:{R} ").strip()
    if not title:
        return

    desc = input(f"  {CYAN}Details (optional):{R} ").strip()

    print(f"  {CYAN}Priorität:{R} {RED}[h]{R}och {YELLOW}[m]{R}ittel {GREEN}[l]{R}ow")
    pc = input(f"  {CYAN}▸{R} ").strip().lower()
    priority = {"h": "high", "l": "low"}.get(pc, "medium")

    tid = create_task(pid, title, desc, priority)
    print(f"  {GREEN}✅ Task erstellt (ID: {tid}){R}")
    input(f"  {DIM}Enter...{R}")


def complete_task_interactive(pid):
    tasks = get_tasks(pid)
    open_tasks = [t for t in tasks if t["status"] != "done"]
    if not open_tasks:
        print(f"\n  {DIM}Alle Tasks erledigt! 🎉{R}")
        input(f"  {DIM}Enter...{R}")
        return

    tid = input(f"\n  {CYAN}Task ID erledigen:{R} ").strip()
    if tid.isdigit():
        task = get_task(int(tid))
        if task and task["project_id"] == pid:
            new_status = "done" if task["status"] != "done" else "todo"
            update_task(int(tid), status=new_status)
            emoji = "✅" if new_status == "done" else "☐"
            print(f"  {GREEN}{emoji} Task aktualisiert!{R}")

            # Projekt auto-complete check
            total, done, _, _ = get_progress(pid)
            if total > 0 and done == total:
                print(f"\n  {GREEN}🎉 Alle Tasks erledigt!{R}")
                ac = input(f"  {CYAN}Projekt als abgeschlossen markieren? (j/n):{R} ").strip().lower()
                if ac in ("j", "ja"):
                    update_project(pid, status="completed")
    input(f"  {DIM}Enter...{R}")


def edit_task_interactive(pid):
    tid = input(f"\n  {CYAN}Task ID bearbeiten:{R} ").strip()
    if not tid.isdigit():
        return

    task = get_task(int(tid))
    if not task or task["project_id"] != pid:
        print(f"  {RED}Task nicht gefunden.{R}")
        input(f"  {DIM}Enter...{R}")
        return

    print(f"\n  {DIM}Aktuell: {task['title']}{R}")
    print(f"  {DIM}Status: {task['status']} | Priorität: {task['priority']}{R}")

    new_title = input(f"  {CYAN}Neuer Titel (Enter=behalten):{R} ").strip()
    if new_title:
        update_task(int(tid), title=new_title)

    print(f"  {CYAN}Status:{R} [t]odo [d]oing [x]done")
    ns = input(f"  {CYAN}▸{R} ").strip().lower()
    if ns in ("t", "d", "x"):
        status = {"t": "todo", "d": "doing", "x": "done"}[ns]
        update_task(int(tid), status=status)

    print(f"  {GREEN}✅ Task aktualisiert!{R}")
    input(f"  {DIM}Enter...{R}")


def delete_task_interactive(pid):
    tid = input(f"\n  {CYAN}Task ID löschen:{R} ").strip()
    if tid.isdigit():
        task = get_task(int(tid))
        if task and task["project_id"] == pid:
            confirm = input(f"  {RED}'{task['title']}' löschen? (j/n):{R} ").strip().lower()
            if confirm in ("j", "ja"):
                delete_task(int(tid))
                print(f"  {GREEN}✅ Gelöscht.{R}")
    input(f"  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  PROJEKT BEARBEITEN
# ══════════════════════════════════════════

def edit_project(pid):
    project = get_project(pid)
    print(f"\n  {DIM}Name: {project['name']}{R}")
    new_name = input(f"  {CYAN}Neuer Name (Enter=behalten):{R} ").strip()
    if new_name:
        update_project(pid, name=new_name)

    new_desc = input(f"  {CYAN}Neue Beschreibung (Enter=behalten):{R} ").strip()
    if new_desc:
        update_project(pid, description=new_desc)

    print(f"  {GREEN}✅ Aktualisiert!{R}")
    input(f"  {DIM}Enter...{R}")


def change_project_status(pid):
    statuses = ["active", "paused", "completed", "archived"]
    print()
    for i, s in enumerate(statuses, 1):
        emoji = STATUS_EMOJI.get(s, "")
        print(f"  {YELLOW}[{i}]{R} {emoji} {s}")

    choice = input(f"\n  {CYAN}▸{R} ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(statuses):
        update_project(pid, status=statuses[int(choice) - 1])
        print(f"  {GREEN}✅ Status geändert!{R}")
    input(f"  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  AI PROJEKT REVIEW
# ══════════════════════════════════════════

def ai_project_review(pid):
    project = get_project(pid)
    tasks = get_tasks(pid)
    total, done, doing, todo = get_progress(pid)

    task_list = ""
    for t in tasks:
        task_list += f"- [{t['status']}] {t['title']} (Priorität: {t['priority']})\n"

    print(f"\n  {CYAN}🤖 AI analysiert Projekt...{R}")

    prompt = f"""Analysiere dieses Softwareprojekt und gib Empfehlungen:

Projekt: {project['name']}
Beschreibung: {project['description']}
Sprache: {project['language']}
Status: {project['status']}
Fortschritt: {done}/{total} Tasks erledigt

Tasks:
{task_list}

Bitte gib:
1. Eine kurze Einschätzung des Fortschritts
2. Mögliche fehlende Tasks
3. Empfehlungen zur Reihenfolge
4. Potenzielle Risiken

Halte es kurz und praktisch."""

    result = chat(prompt, system="Du bist ein erfahrener Projektmanager und Software-Architekt.")

    print(f"\n  {GREEN}{BOLD}📊 AI Projekt Review:{R}\n")
    for line in result.split('\n'):
        print(f"  {line}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════

def project_dashboard():
    clear()
    header("Dashboard")

    projects = get_projects()
    active = [p for p in projects if p["status"] == "active"]
    paused = [p for p in projects if p["status"] == "paused"]
    completed = [p for p in projects if p["status"] == "completed"]

    # Gesamtstatistik
    total_tasks = 0
    done_tasks = 0
    for p in projects:
        t, d, _, _ = get_progress(p["id"])
        total_tasks += t
        done_tasks += d

    print(f"""
  {BOLD}Übersicht:{R}
  📁 {len(projects)} Projekte  │  ✅ {len(completed)} abgeschlossen
  📋 {total_tasks} Tasks      │  ✅ {done_tasks} erledigt
  {progress_bar(done_tasks, total_tasks, 30)}
    """)

    if active:
        print(f"  {GREEN}{BOLD}🟢 Aktive Projekte:{R}")
        show_project_list(active)

    if paused:
        print(f"\n  {YELLOW}{BOLD}⏸️  Pausiert:{R}")
        show_project_list(paused)

    if completed:
        print(f"\n  {DIM}✅ Abgeschlossen: {len(completed)}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  HAUPTMENÜ
# ══════════════════════════════════════════

def projects_menu():
    while True:
        clear()
        header("Projekt Manager")

        projects = get_projects()
        active = [p for p in projects if p["status"] in ("active", "paused")]

        if active:
            print()
            show_project_list(active)

        print(f"""
  {YELLOW}[n]{R} ➕ Neues Projekt        {YELLOW}[d]{R} 📊 Dashboard
  {YELLOW}[a]{R} 📁 Alle Projekte        {YELLOW}[#]{R} Projekt öffnen (ID)
  {YELLOW}[0]{R} Zurück
        """)

        choice = input(f"  {CYAN}▸{R} ").strip().lower()

        if choice == "n":
            new_project()
        elif choice == "d":
            project_dashboard()
        elif choice == "a":
            clear()
            header("Alle Projekte")
            show_project_list(get_projects())
            print()
            pid = input(f"  {CYAN}Projekt öffnen (ID/0=zurück):{R} ").strip()
            if pid.isdigit() and pid != "0":
                project_detail(int(pid))
        elif choice.isdigit() and choice != "0":
            project_detail(int(choice))
        elif choice == "0":
            break


# ══════════════════════════════════════════
#  SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    from fred_db import init_db
    init_db()

    print(f"{MAGENTA}{BOLD}📁 Fred Projekt Manager{R}")
    print(f"{'=' * 40}")

    projects = get_projects()
    total_tasks = 0
    done_tasks = 0
    for p in projects:
        t, d, _, _ = get_progress(p["id"])
        total_tasks += t
        done_tasks += d

    print(f"\n  📁 {len(projects)} Projekte")
    print(f"  📋 {total_tasks} Tasks ({done_tasks} erledigt)")

    print(f"\n  Funktionen:")
    print(f"    ➕ Projekte erstellen & verwalten")
    print(f"    📋 Tasks mit Prioritäten")
    print(f"    📊 Fortschritts-Tracking")
    print(f"    🤖 AI Task-Vorschläge & Reviews")
    print(f"    📊 Dashboard")

    print(f"\n  ✅ fred_projects.py geladen!")
