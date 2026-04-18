import os
import json
import subprocess
import sqlite3
import glob
import re
import requests
from datetime import datetime

# ============================================
# FRED AGENT v2.0 - OpenClaw-Style
# ============================================

# --- Konfiguration ---
HOME = os.path.expanduser("~")
FRED_DIR = os.path.join(HOME, "fred")
CONFIG_FILE = os.path.join(FRED_DIR, "fred_config.json")
MEMORY_DB = os.path.join(FRED_DIR, "fred_memory.db")
SKILLS_DIR = os.path.join(FRED_DIR, "skills")
LOG_FILE = os.path.join(FRED_DIR, "fred.log")
MODEL = "llama3"

# --- Logging ---
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

# --- Config ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_api_key():
    key = os.environ.get("OLLAMA_API_KEY", "")
    if key:
        return key
    return load_config().get("api_key", "")

# ============================================
# GEDAECHTNIS (Persistentes Memory)
# ============================================
def init_db():
    os.makedirs(FRED_DIR, exist_ok=True)
    os.makedirs(SKILLS_DIR, exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, role TEXT, content TEXT, session TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE, value TEXT, updated TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT, status TEXT DEFAULT 'offen',
        created TEXT, due TEXT, result TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS action_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, skill TEXT, params TEXT, result TEXT
    )""")
    conn.commit()
    conn.close()

class Memory:
    @staticmethod
    def save_msg(role, content, session):
        conn = sqlite3.connect(MEMORY_DB)
        conn.execute("INSERT INTO chat (ts,role,content,session) VALUES (?,?,?,?)",
                      (datetime.now().isoformat(), role, content, session))
        conn.commit()
        conn.close()

    @staticmethod
    def get_history(limit=20):
        conn = sqlite3.connect(MEMORY_DB)
        rows = conn.execute(
            "SELECT role, content FROM chat ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    @staticmethod
    def set_fact(key, value):
        conn = sqlite3.connect(MEMORY_DB)
        conn.execute("INSERT OR REPLACE INTO facts (key,value,updated) VALUES (?,?,?)",
                      (key.lower().strip(), value, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @staticmethod
    def get_fact(key):
        conn = sqlite3.connect(MEMORY_DB)
        row = conn.execute("SELECT value FROM facts WHERE key=?", (key.lower().strip(),)).fetchone()
        conn.close()
        return row[0] if row else None

    @staticmethod
    def all_facts():
        conn = sqlite3.connect(MEMORY_DB)
        rows = conn.execute("SELECT key, value FROM facts ORDER BY key").fetchall()
        conn.close()
        return dict(rows)

    @staticmethod
    def add_task(text, due=None):
        conn = sqlite3.connect(MEMORY_DB)
        conn.execute("INSERT INTO tasks (text,status,created,due) VALUES (?,?,?,?)",
                      (text, "offen", datetime.now().isoformat(), due))
        conn.commit()
        conn.close()

    @staticmethod
    def get_tasks(status=None):
        conn = sqlite3.connect(MEMORY_DB)
        if status:
            rows = conn.execute("SELECT id,text,status,created,due FROM tasks WHERE status=?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT id,text,status,created,due FROM tasks ORDER BY id").fetchall()
        conn.close()
        return rows

    @staticmethod
    def finish_task(tid, result=""):
        conn = sqlite3.connect(MEMORY_DB)
        conn.execute("UPDATE tasks SET status='erledigt', result=? WHERE id=?", (result, tid))
        conn.commit()
        conn.close()

    @staticmethod
    def log_action(skill, params, result):
        conn = sqlite3.connect(MEMORY_DB)
        conn.execute("INSERT INTO action_log (ts,skill,params,result) VALUES (?,?,?,?)",
                      (datetime.now().isoformat(), skill, json.dumps(params, ensure_ascii=False), result[:500]))
        conn.commit()
        conn.close()

# ============================================
# SKILLS
# ============================================
DANGEROUS = ["rm -rf /", "mkfs", "dd if=", ":(){:", "chmod -R 777 /",
             "shutdown", "reboot", "init 0", "init 6", "wipefs"]

def is_dangerous(cmd):
    cmd_lower = cmd.lower().strip()
    for d in DANGEROUS:
        if d in cmd_lower:
            return True
    return False

def run_shell(command, timeout=30):
    if is_dangerous(command):
        return "🛑 BLOCKIERT: Dieser Befehl ist zu gefährlich!"
    try:
        r = subprocess.run(command, shell=True, capture_output=True,
                           text=True, timeout=timeout, cwd=HOME)
        out = (r.stdout + r.stderr).strip()
        return out[:3000] if out else "(Kein Output)"
    except subprocess.TimeoutExpired:
        return "⏰ Timeout nach {}s".format(timeout)
    except Exception as e:
        return f"❌ Fehler: {e}"

def read_file(path):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"❌ Datei nicht gefunden: {path}"
    try:
        with open(path, "r", errors="replace") as f:
            text = f.read()
        if len(text) > 4000:
            return text[:4000] + "\n... (gekürzt)"
        return text
    except Exception as e:
        return f"❌ Fehler: {e}"

def write_file(path, content):
    path = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"✅ Gespeichert: {path} ({len(content)} Zeichen)"
    except Exception as e:
        return f"❌ Fehler: {e}"

def find_files(pattern, directory="~"):
    directory = os.path.expanduser(directory)
    try:
        matches = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        if not matches:
            return "Keine Dateien gefunden."
        return "\n".join(matches[:30])
    except Exception as e:
        return f"❌ Fehler: {e}"

def fetch_web(url):
    try:
        headers = {"User-Agent": "Fred-Agent/2.0"}
        resp = requests.get(url, timeout=15, headers=headers)
        text = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:4000] if text else "(Leere Seite)"
    except Exception as e:
        return f"❌ Fehler: {e}"

def system_info():
    parts = []
    parts.append("📊 SYSTEM INFO:")
    parts.append(run_shell("hostname && uname -srm"))
    parts.append("---")
    parts.append(run_shell("df -h / --output=size,used,avail,pcent | tail -1"))
    parts.append("---")
    parts.append(run_shell("free -h | grep Mem"))
    parts.append("---")
    parts.append(run_shell("uptime -p"))
    return "\n".join(parts)

# Skill-Registry
SKILLS = {
    "shell": {
        "func": lambda p: run_shell(p["command"], p.get("timeout", 30)),
        "desc": "Shell-Befehl ausführen",
        "params": "command, timeout(optional)"
    },
    "read_file": {
        "func": lambda p: read_file(p["path"]),
        "desc": "Datei lesen",
        "params": "path"
    },
    "write_file": {
        "func": lambda p: write_file(p["path"], p["content"]),
        "desc": "Datei schreiben",
        "params": "path, content"
    },
    "find_files": {
        "func": lambda p: find_files(p["pattern"], p.get("directory", "~")),
        "desc": "Dateien suchen",
        "params": "pattern, directory(optional)"
    },
    "web": {
        "func": lambda p: fetch_web(p["url"]),
        "desc": "Webseite lesen",
        "params": "url"
    },
    "remember": {
        "func": lambda p: (Memory.set_fact(p["key"], p["value"]), f"✅ Gemerkt: {p['key']}")[1],
        "desc": "Information merken",
        "params": "key, value"
    },
    "recall": {
        "func": lambda p: Memory.get_fact(p["key"]) or f"Nichts zu '{p['key']}' gespeichert.",
        "desc": "Information abrufen",
        "params": "key"
    },
    "recall_all": {
        "func": lambda p: json.dumps(Memory.all_facts(), indent=2, ensure_ascii=False) or "Leer.",
        "desc": "Alle gespeicherten Infos",
        "params": "(keine)"
    },
    "add_task": {
        "func": lambda p: (Memory.add_task(p["text"], p.get("due")), f"✅ Aufgabe erstellt: {p['text']}")[1],
        "desc": "Aufgabe erstellen",
        "params": "text, due(optional)"
    },
    "list_tasks": {
        "func": lambda p: format_tasks(Memory.get_tasks(p.get("status", "offen"))),
        "desc": "Aufgaben anzeigen",
        "params": "status(optional)"
    },
    "complete_task": {
        "func": lambda p: (Memory.finish_task(p["id"], p.get("result", "")), f"✅ Aufgabe {p['id']} erledigt.")[1],
        "desc": "Aufgabe abschließen",
        "params": "id, result(optional)"
    },
    "sysinfo": {
        "func": lambda p: system_info(),
        "desc": "Systeminformationen",
        "params": "(keine)"
    }
}

def format_tasks(tasks):
    if not tasks:
        return "Keine Aufgaben gefunden."
    lines = ["📋 Aufgaben:"]
    for t in tasks:
        icon = "✅" if t[2] == "erledigt" else "📌"
        lines.append(f"  {icon} [{t[0]}] {t[1]} ({t[2]})")
    return "\n".join(lines)

# ============================================
# LLM VERBINDUNG
# ============================================
def build_system_prompt():
    facts = Memory.all_facts()
    tasks = Memory.get_tasks("offen")

    skills_text = "\n".join([f"  - {k}: {v['desc']} | Parameter: {v['params']}" for k, v in SKILLS.items()])

    facts_text = ""
    if facts:
        facts_text = "\n\nGESPEICHERTE INFOS UEBER DEN NUTZER:\n" + \
            "\n".join([f"  {k}: {v}" for k, v in facts.items()])

    tasks_text = ""
    if tasks:
        tasks_text = "\n\nOFFENE AUFGABEN:\n" + \
            "\n".join([f"  [{t[0]}] {t[1]}" for t in tasks])

    return f"""Du bist Fred, ein autonomer KI-Agent.
Du fuehrst AKTIV Aufgaben aus - du bist KEIN reiner Chatbot!

AKTUELL: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr

DEINE SKILLS:
{skills_text}

SKILL AUSFUEHREN - Schreibe genau dieses Format:
[ACTION]
{{"skill": "name", "params": {{"key": "value"}}}}
[/ACTION]

REGELN:
1. Nutze Skills AKTIV wenn es Sinn macht
2. Mehrere Actions pro Antwort sind erlaubt
3. Erklaere kurz was du tust
4. Antworte auf Deutsch
5. Merke dir wichtige Infos ueber den Nutzer
6. Bei gefaehrlichen Befehlen: frage vorher nach
7. Sei kompakt und hilfreich
{facts_text}
{tasks_text}"""

def call_ollama(messages):
    api_key = get_api_key()

    # Versuch 1: Ollama Cloud API
    if api_key:
        try:
            from ollama import Client
            client = Client(host="https://api.ollama.com",
                          headers={"Authorization": f"Bearer {api_key}"})
            resp = client.chat(MODEL, messages=messages)
            return resp["message"]["content"]
        except:
            pass

    # Versuch 2: Lokaler Ollama HTTP
    try:
        resp = requests.post("http://localhost:11434/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False
        }, timeout=120)
        if resp.status_code == 200:
            return resp.json()["message"]["content"]
    except:
        pass

    # Versuch 3: Ollama CLI
    try:
        prompt = messages[-1]["content"]
        r = subprocess.run(["ollama", "run", MODEL, prompt],
                          capture_output=True, text=True, timeout=120)
        if r.stdout.strip():
            return r.stdout.strip()
    except:
        pass

    return "❌ Keine LLM-Verbindung! Starte Ollama mit 'ollama serve' oder setze API Key mit 'key'."

# ============================================
# ACTION PARSER & EXECUTOR
# ============================================
def extract_actions(text):
    pattern = r'\[ACTION\]\s*\n?(.*?)\n?\[/ACTION\]'
    matches = re.findall(pattern, text, re.DOTALL)
    actions = []
    for m in matches:
        try:
            data = json.loads(m.strip())
            actions.append(data)
        except json.JSONDecodeError:
            log(f"JSON parse error: {m[:100]}")
    return actions

def execute_actions(actions):
    results = []
    for act in actions:
        skill_name = act.get("skill", "")
        params = act.get("params", {})

        if skill_name not in SKILLS:
            results.append({"skill": skill_name, "ok": False, "result": f"Unbekannter Skill: {skill_name}"})
            continue

        try:
            result = SKILLS[skill_name]["func"](params)
            Memory.log_action(skill_name, params, str(result))
            log(f"SKILL OK: {skill_name}({params})")
            results.append({"skill": skill_name, "ok": True, "result": result})
        except Exception as e:
            log(f"SKILL FAIL: {skill_name} -> {e}")
            results.append({"skill": skill_name, "ok": False, "result": str(e)})

    return results

def clean_response(text):
    return re.sub(r'\[ACTION\]\s*\n?.*?\n?\[/ACTION\]', '', text, flags=re.DOTALL).strip()

# ============================================
# AGENT LOOP
# ============================================
def print_banner():
    print()
    print("╔══════════════════════════════════════════╗")
    print("║     🤖 FRED AGENT v2.0                  ║")
    print("║     Autonomer KI-Assistent               ║")
    print("╠══════════════════════════════════════════╣")
    print("║  Befehle:                                ║")
    print("║    exit    - Beenden                     ║")
    print("║    key     - API Key setzen              ║")
    print("║    skills  - Alle Skills anzeigen        ║")
    print("║    tasks   - Aufgaben anzeigen           ║")
    print("║    facts   - Gespeicherte Infos          ║")
    print("║    log     - Letzte Aktionen             ║")
    print("║    clear   - Chat-Verlauf loeschen       ║")
    print("╚══════════════════════════════════════════╝")
    print()

def cmd_set_key():
    print("\n🔑 API Key eingeben (Enter = abbrechen):")
    key = input("   > ").strip()
    if key:
        cfg = load_config()
        cfg["api_key"] = key
        save_config(cfg)
        print("   ✅ Gespeichert!\n")
    else:
        print("   Abgebrochen.\n")

def cmd_skills():
    print("\n📦 Skills:")
    for name, info in SKILLS.items():
        print(f"   • {name:15s} - {info['desc']}")
    print()

def cmd_tasks():
    tasks = Memory.get_tasks()
    if not tasks:
        print("\n   Keine Aufgaben.\n")
        return
    print(format_tasks(tasks))
    print()

def cmd_facts():
    facts = Memory.all_facts()
    if not facts:
        print("\n   Noch nichts gespeichert.\n")
        return
    print("\n🧠 Gespeicherte Infos:")
    for k, v in facts.items():
        print(f"   {k}: {v}")
    print()

def cmd_log():
    conn = sqlite3.connect(MEMORY_DB)
    rows = conn.execute("SELECT ts, skill, params, result FROM action_log ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    if not rows:
        print("\n   Noch keine Aktionen.\n")
        return
    print("\n📜 Letzte Aktionen:")
    for r in reversed(rows):
        print(f"   [{r[0][:16]}] {r[1]}: {r[3][:80]}")
    print()

def agent_main(db_path=None):
    init_db()
    print_banner()

    api_key = get_api_key()
    if not api_key:
        print("⚠️  Kein API Key! Tippe 'key' oder starte lokales Ollama.\n")

    session = datetime.now().strftime("%Y%m%d_%H%M%S")
    max_steps = 5  # Max autonome Schritte pro Anfrage

    while True:
        try:
            user_input = input("Du: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Bis bald!")
            break

        if not user_input:
            continue

        low = user_input.lower()
        if low in ("exit", "quit", "q", "bye"):
            print("👋 Bis bald!")
            break
        elif low == "key":
            cmd_set_key()
            continue
        elif low == "skills":
            cmd_skills()
            continue
        elif low == "tasks":
            cmd_tasks()
            continue
        elif low == "facts":
            cmd_facts()
            continue
        elif low == "log":
            cmd_log()
            continue
        elif low == "clear":
            conn = sqlite3.connect(MEMORY_DB)
            conn.execute("DELETE FROM chat")
            conn.commit()
            conn.close()
            print("🗑️  Chat-Verlauf gelöscht.\n")
            continue

        # Nachricht speichern
        Memory.save_msg("user", user_input, session)

        # Kontext bauen
        system_prompt = build_system_prompt()
        history = Memory.get_history(20)
        messages = [{"role": "system", "content": system_prompt}] + history

        # Multi-Step Loop
        step = 0
        while step < max_steps:
            step += 1

            print(f"\nFred: ", end="", flush=True)
            response = call_ollama(messages)

            # Actions extrahieren
            actions = extract_actions(response)
            clean = clean_response(response)

            if clean:
                print(clean)

            if not actions:
                # Keine Actions -> fertig
                Memory.save_msg("assistant", response, session)
                break

            # Actions ausfuehren
            results = execute_actions(actions)
            for r in results:
                icon = "✅" if r["ok"] else "❌"
                print(f"\n   {icon} [{r['skill']}]: {r['result'][:200]}")

            Memory.save_msg("assistant", response, session)

            # Ergebnisse zurueck ans LLM
            results_json = json.dumps(results, ensure_ascii=False, indent=2)
            followup = f"[SYSTEM] Ergebnisse von Schritt {step}:\n{results_json}\n\nFahre fort oder antworte dem Nutzer."
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": followup})

            if step >= max_steps:
                print(f"\n   ⚠️ Max Schritte ({max_steps}) erreicht.")

        print()

# Alias
agent_loop = agent_main

if __name__ == "__main__":
    agent_main()
