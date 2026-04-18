#!/usr/bin/env python3
"""Fred Logging - Unabhängiges Log-System"""

import os
import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "fred.log")
MAX_SIZE = 1_000_000  # 1MB, dann rotieren

def _ensure_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def log(level, module, message):
    """Log-Eintrag schreiben. Level: INFO, WARN, ERROR, DEBUG"""
    _ensure_dir()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level:5s}] [{module}] {message}\n"
    
    # Rotation bei Überschreitung
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_SIZE:
        backup = LOG_FILE + ".old"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(LOG_FILE, backup)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def info(module, msg):
    log("INFO", module, msg)

def warn(module, msg):
    log("WARN", module, msg)

def error(module, msg):
    log("ERROR", module, msg)

def debug(module, msg):
    log("DEBUG", module, msg)

def show_log(lines=50):
    """Letzte n Zeilen anzeigen"""
    if not os.path.exists(LOG_FILE):
        print("  Noch keine Logs vorhanden.")
        return
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    for line in all_lines[-lines:]:
        print(f"  {line.rstrip()}")

def clear_log():
    """Log löschen"""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        print("  Log gelöscht.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_log()
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        show_log(int(sys.argv[1]))
    else:
        show_log()
