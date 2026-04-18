#!/usr/bin/env python3
"""
FRED v5.0 Core - Datenbank, Menu, Utilities
"""

import os
import sys
import json
import time
import socket
import subprocess
import re
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.text import Text
    from rich.align import Align
    from rich import box
except ImportError:
    print("FEHLER: python3-rich fehlt!")
    print("sudo apt install python3-rich")
    sys.exit(1)

console = Console()


# ============================================================
# DATENBANK
# ============================================================

class FredDB:
    def __init__(self):
        self.base = Path.home() / ".fred"
        self.base.mkdir(exist_ok=True)
        self.files = {
            'config':    self.base / "config.json",
            'history':   self.base / "history.json",
            'ssh':       self.base / "ssh.json",
            'notes':     self.base / "notes.json",
            'bookmarks': self.base / "bookmarks.json",
            'watchdog':  self.base / "watchdog.json",
        }
        self.defaults = {
            'config': {"theme": "standard", "log_level": "normal", "max_history": 200},
            'history': [],
            'ssh': [],
            'notes': [],
            'bookmarks': [],
            'watchdog': [],
        }

    def load(self, name):
        f = self.files.get(name)
        if not f or not f.exists():
            return self.defaults.get(name, {})
        try:
            return json.loads(f.read_text())
        except Exception:
            return self.defaults.get(name, {})

    def save(self, name, data):
        f = self.files.get(name)
        if f:
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def add_history(self, action, detail=""):
        h = self.load('history')
        h.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "detail": str(detail)[:200]
        })
        cfg = self.load('config')
        mx = cfg.get('max_history', 200)
        if len(h) > mx:
            h = h[-mx:]
        self.save('history', h)


# ============================================================
# UTILITIES
# ============================================================

class Utils:
    @staticmethod
    def run(cmd, timeout=30):
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            return r.stdout.strip(), r.stderr.strip(), r.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", 1
        except Exception as e:
            return "", str(e), 1

    @staticmethod
    def run_live(cmd):
        try:
            os.system(cmd)
        except KeyboardInterrupt:
            console.print("\n  [dim]Abgebrochen[/dim]")

    @staticmethod
    def is_installed(prog):
        out, _, rc = Utils.run(f"which {prog}")
        return rc == 0

    @staticmethod
    def require(prog, pkg=None):
        if not Utils.is_installed(prog):
            pkg = pkg or prog
            console.print(f"  [red]{prog} fehlt![/red] Installiere mit: sudo apt install {pkg}")
            return False
        return True

    @staticmethod
    def pause():
        console.input("\n  [dim]Enter zum Fortfahren...[/dim]")

    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def get_gateway():
        out, _, _ = Utils.run("ip route | grep default | awk '{print $3}'")
        return out or "unbekannt"

    @staticmethod
    def get_subnet():
        ip = Utils.get_local_ip()
        parts = ip.rsplit('.', 1)
        return parts[0] + ".0/24" if len(parts) == 2 else "192.168.1.0/24"


# ============================================================
# MENU SYSTEM
# ============================================================

class MenuItem:
    def __init__(self, key, title, desc, action=None, submenu=None):
        self.key = key
        self.title = title
        self.desc = desc
        self.action = action
        self.submenu = submenu


class Menu:
    def __init__(self, title, db, is_root=False):
        self.title = title
        self.db = db
        self.items = []
        self.is_root = is_root

    def add(self, key, title, desc="", action=None, submenu=None):
        self.items.append(MenuItem(key, title, desc, action, submenu))

    def show(self):
        console.print()
        t = Table(
            title=f"  {self.title}",
            box=box.ROUNDED,
            show_header=False,
            padding=(0, 2),
            title_style="bold cyan"
        )
        t.add_column("Nr", style="bold yellow", width=4)
        t.add_column("Funktion", style="bold white", width=24)
        t.add_column("Beschreibung", style="dim")

        for item in self.items:
            marker = " >>" if item.submenu else "   "
            t.add_row(f"[{item.key}]", f"{marker} {item.title}", item.desc)

        console.print(t)

        if self.is_root:
            console.print("  [dim]q = Beenden[/dim]")
        else:
            console.print("  [dim]0 = Zurueck  q = Beenden[/dim]")

    def run(self):
        while True:
            self.show()
            try:
                choice = Prompt.ask("\n  Auswahl").strip().lower()
            except (KeyboardInterrupt, EOFError):
                if self.is_root:
                    console.print("\n  [dim]Fred beendet.[/dim]\n")
                    sys.exit(0)
                return

            if choice == 'q':
                if self.is_root:
                    console.print("\n  [dim]Fred beendet.[/dim]\n")
                    sys.exit(0)
                return

            if choice == '0' and not self.is_root:
                return

            found = False
            for item in self.items:
                if item.key == choice:
                    found = True
                    if item.submenu:
                        item.submenu.run()
                    elif item.action:
                        try:
                            self.db.add_history(item.title)
                            item.action()
                        except KeyboardInterrupt:
                            console.print("\n  [dim]Abgebrochen[/dim]")
                        except Exception as e:
                            console.print(f"  [red]Fehler: {e}[/red]")
                    break

            if not found:
                console.print("  [red]Ungueltige Auswahl[/red]")


def init_fred():
    db = FredDB()
    return db
