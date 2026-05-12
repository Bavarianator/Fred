"""
FRED v2.0 - Datenbank Layer
Alle Tabellen, alle Queries, ein Modul.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.expanduser("~/fred/fred.db")


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS providers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        base_url TEXT,
        api_key TEXT DEFAULT '',
        model TEXT DEFAULT '',
        active INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT 'Neuer Chat',
        mode TEXT DEFAULT 'normal',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        role TEXT,
        content TEXT,
        tokens INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        category TEXT DEFAULT 'allgemein',
        tags TEXT DEFAULT '',
        pinned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT DEFAULT '',
        status TEXT DEFAULT 'aktiv',
        path TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        text TEXT,
        done INTEGER DEFAULT 0,
        priority INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS snippets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        language TEXT DEFAULT 'python',
        code TEXT,
        description TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Profile management table
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT DEFAULT '',
        settings TEXT DEFAULT '{}',
        vault_enabled INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Vault entries table (metadata only, actual keys stored encrypted in file)
    c.execute('''CREATE TABLE IF NOT EXISTS vault_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        service_name TEXT,
        description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    )''')

    # Remote tokens table
    c.execute('''CREATE TABLE IF NOT EXISTS remote_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_hash TEXT UNIQUE,
        client_name TEXT,
        expires_at TIMESTAMP,
        last_used TIMESTAMP,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Standard-Provider anlegen
    defaults = [
        ('OpenAI', 'https://api.openai.com/v1', '', 'gpt-4o-mini'),
        ('Groq', 'https://api.groq.com/openai/v1', '', 'llama-3.1-70b-versatile'),
        ('Ollama', 'http://localhost:11434', '', 'llama3.1'),
        ('OpenRouter', 'https://openrouter.ai/api/v1', '', 'meta-llama/llama-3.1-8b-instruct:free'),
    ]
    for name, url, key, model in defaults:
        c.execute('''INSERT OR IGNORE INTO providers (name, base_url, api_key, model)
                     VALUES (?, ?, ?, ?)''', (name, url, key, model))

    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════

def get_setting(key, default=""):
    conn = connect()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key, value):
    conn = connect()
    conn.execute('''INSERT INTO settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=?, updated_at=?''',
                 (key, str(value), datetime.now(), str(value), datetime.now()))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  PROVIDERS
# ══════════════════════════════════════════

def get_providers():
    conn = connect()
    rows = conn.execute("SELECT * FROM providers ORDER BY name").fetchall()
    conn.close()
    return rows


def get_active_provider():
    conn = connect()
    row = conn.execute("SELECT * FROM providers WHERE active=1 LIMIT 1").fetchone()
    conn.close()
    return row


def set_active_provider(provider_id):
    conn = connect()
    conn.execute("UPDATE providers SET active=0")
    conn.execute("UPDATE providers SET active=1 WHERE id=?", (provider_id,))
    conn.commit()
    conn.close()


def update_provider(provider_id, api_key=None, model=None, base_url=None):
    conn = connect()
    if api_key is not None:
        conn.execute("UPDATE providers SET api_key=? WHERE id=?", (api_key, provider_id))
    if model is not None:
        conn.execute("UPDATE providers SET model=? WHERE id=?", (model, provider_id))
    if base_url is not None:
        conn.execute("UPDATE providers SET base_url=? WHERE id=?", (base_url, provider_id))
    conn.commit()
    conn.close()


def add_provider(name, base_url, api_key="", model=""):
    conn = connect()
    conn.execute("INSERT INTO providers (name, base_url, api_key, model) VALUES (?,?,?,?)",
                 (name, base_url, api_key, model))
    conn.commit()
    conn.close()


def delete_provider(provider_id):
    conn = connect()
    conn.execute("DELETE FROM providers WHERE id=?", (provider_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  CHATS
# ══════════════════════════════════════════

def create_chat(title="Neuer Chat", mode="normal"):
    conn = connect()
    c = conn.execute("INSERT INTO chats (title, mode) VALUES (?, ?)", (title, mode))
    chat_id = c.lastrowid
    conn.commit()
    conn.close()
    return chat_id


def get_chats(limit=50):
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM chats ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows


def get_chat(chat_id):
    conn = connect()
    row = conn.execute("SELECT * FROM chats WHERE id=?", (chat_id,)).fetchone()
    conn.close()
    return row


def update_chat_title(chat_id, title):
    conn = connect()
    conn.execute("UPDATE chats SET title=?, updated_at=? WHERE id=?",
                 (title, datetime.now(), chat_id))
    conn.commit()
    conn.close()


def delete_chat(chat_id):
    conn = connect()
    conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  MESSAGES
# ══════════════════════════════════════════

def save_message(chat_id, role, content, tokens=0):
    conn = connect()
    conn.execute("INSERT INTO messages (chat_id, role, content, tokens) VALUES (?,?,?,?)",
                 (chat_id, role, content, tokens))
    conn.execute("UPDATE chats SET updated_at=? WHERE id=?", (datetime.now(), chat_id))
    conn.commit()
    conn.close()


def get_messages(chat_id, limit=100):
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM messages WHERE chat_id=? ORDER BY created_at ASC LIMIT ?",
        (chat_id, limit)
    ).fetchall()
    conn.close()
    return rows


# ══════════════════════════════════════════
#  NOTES
# ══════════════════════════════════════════

def create_note(title, content="", category="allgemein", tags=""):
    conn = connect()
    c = conn.execute("INSERT INTO notes (title, content, category, tags) VALUES (?,?,?,?)",
                     (title, content, category, tags))
    note_id = c.lastrowid
    conn.commit()
    conn.close()
    return note_id


def get_notes(category=None, search=None):
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


def update_note(note_id, title=None, content=None, category=None, tags=None, pinned=None):
    conn = connect()
    if title is not None:
        conn.execute("UPDATE notes SET title=?, updated_at=? WHERE id=?", (title, datetime.now(), note_id))
    if content is not None:
        conn.execute("UPDATE notes SET content=?, updated_at=? WHERE id=?", (content, datetime.now(), note_id))
    if category is not None:
        conn.execute("UPDATE notes SET category=? WHERE id=?", (category, note_id))
    if tags is not None:
        conn.execute("UPDATE notes SET tags=? WHERE id=?", (tags, note_id))
    if pinned is not None:
        conn.execute("UPDATE notes SET pinned=? WHERE id=?", (pinned, note_id))
    conn.commit()
    conn.close()


def delete_note(note_id):
    conn = connect()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  PROJECTS & TODOS
# ══════════════════════════════════════════

def create_project(name, description="", path=""):
    conn = connect()
    c = conn.execute("INSERT INTO projects (name, description, path) VALUES (?,?,?)",
                     (name, description, path))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_projects(status=None):
    conn = connect()
    if status:
        rows = conn.execute("SELECT * FROM projects WHERE status=? ORDER BY updated_at DESC",
                           (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    conn.close()
    return rows


def get_project(project_id):
    conn = connect()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    conn.close()
    return row


def update_project(project_id, name=None, description=None, status=None, path=None):
    conn = connect()
    if name is not None:
        conn.execute("UPDATE projects SET name=?, updated_at=? WHERE id=?", (name, datetime.now(), project_id))
    if description is not None:
        conn.execute("UPDATE projects SET description=?, updated_at=? WHERE id=?", (description, datetime.now(), project_id))
    if status is not None:
        conn.execute("UPDATE projects SET status=? WHERE id=?", (status, project_id))
    if path is not None:
        conn.execute("UPDATE projects SET path=? WHERE id=?", (path, project_id))
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = connect()
    conn.execute("DELETE FROM todos WHERE project_id=?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


def add_todo(project_id, text, priority=0):
    conn = connect()
    conn.execute("INSERT INTO todos (project_id, text, priority) VALUES (?,?,?)",
                 (project_id, text, priority))
    conn.commit()
    conn.close()


def get_todos(project_id):
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM todos WHERE project_id=? ORDER BY done ASC, priority DESC, created_at ASC",
        (project_id,)
    ).fetchall()
    conn.close()
    return rows


def toggle_todo(todo_id):
    conn = connect()
    row = conn.execute("SELECT done FROM todos WHERE id=?", (todo_id,)).fetchone()
    if row:
        new_val = 0 if row['done'] else 1
        conn.execute("UPDATE todos SET done=? WHERE id=?", (new_val, todo_id))
    conn.commit()
    conn.close()


def delete_todo(todo_id):
    conn = connect()
    conn.execute("DELETE FROM todos WHERE id=?", (todo_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  SNIPPETS
# ══════════════════════════════════════════

def create_snippet(title, code, language="python", description="", tags=""):
    conn = connect()
    c = conn.execute(
        "INSERT INTO snippets (title, code, language, description, tags) VALUES (?,?,?,?,?)",
        (title, code, language, description, tags))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_snippets(language=None, search=None):
    conn = connect()
    if search:
        rows = conn.execute(
            "SELECT * FROM snippets WHERE title LIKE ? OR code LIKE ? OR tags LIKE ? ORDER BY created_at DESC",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    elif language:
        rows = conn.execute(
            "SELECT * FROM snippets WHERE language=? ORDER BY created_at DESC",
            (language,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM snippets ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_snippet(snippet_id):
    conn = connect()
    row = conn.execute("SELECT * FROM snippets WHERE id=?", (snippet_id,)).fetchone()
    conn.close()
    return row


def delete_snippet(snippet_id):
    conn = connect()
    conn.execute("DELETE FROM snippets WHERE id=?", (snippet_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════
#  STATS & BACKUP
# ══════════════════════════════════════════

def db_stats():
    conn = connect()
    stats = {}
    for table in ['chats', 'messages', 'notes', 'projects', 'todos', 'snippets', 'providers']:
        row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
        stats[table] = row['cnt']
    stats['size_mb'] = round(os.path.getsize(DB_PATH) / 1024 / 1024, 2) if os.path.exists(DB_PATH) else 0
    conn.close()
    return stats


def backup_db(backup_path=None):
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.expanduser(f"~/fred/backups/fred_backup_{timestamp}.db")
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


# ══════════════════════════════════════════
#  SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    print("Initialisiere Fred Datenbank...")
    init_db()

    stats = db_stats()
    print(f"Datenbank: {DB_PATH}")
    print(f"Groesse: {stats['size_mb']} MB")

    providers = get_providers()
    print(f"{len(providers)} Provider konfiguriert:")
    for p in providers:
        status = "AKTIV" if p['active'] else "  -  "
        print(f"  [{status}] {p['name']} -> {p['base_url']}")

    print("\nfred_db.py OK!")
