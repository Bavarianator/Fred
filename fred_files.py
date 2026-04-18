#!/usr/bin/env python3
"""FRED v5.0 - Datei-Modul"""

import os
import time
from fred_core import FredDB, Utils, console

try:
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.table import Table
    from rich import box
except ImportError:
    pass


class FileManager:
    def __init__(self, db: FredDB):
        self.db = db

    def menu(self):
        while True:
            console.clear()
            console.print("\n  [bold cyan]== Datei-Manager ==[/bold cyan]\n")
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            table.add_column(style="bold yellow", width=4)
            table.add_column(style="white")
            table.add_row("1", "Verzeichnis auflisten")
            table.add_row("2", "Datei suchen (Name)")
            table.add_row("3", "Text in Dateien suchen")
            table.add_row("4", "Datei/Ordner kopieren")
            table.add_row("5", "Datei/Ordner verschieben")
            table.add_row("6", "Datei/Ordner loeschen")
            table.add_row("7", "Rechte aendern")
            table.add_row("8", "Besitzer aendern")
            table.add_row("9", "Datei-Info")
            table.add_row("10", "Grosse Dateien finden")
            table.add_row("11", "Doppelte Dateien finden")
            table.add_row("12", "Verzeichnis-Groesse")
            table.add_row("13", "Backup erstellen (tar.gz)")
            table.add_row("14", "Backup entpacken")
            table.add_row("15", "Leere Dateien/Ordner finden")
            table.add_row("16", "Zuletzt geaenderte Dateien")
            table.add_row("0", "Zurueck")
            console.print(table)

            c = Prompt.ask("  Dateien", default="0")

            if c == "0":
                return
            elif c == "1":
                path = Prompt.ask("  Verzeichnis", default=".")
                self.db.add_history("dateien", f"ls {path}")
                Utils.run_live(f"ls -lah --color=auto {path}")
                Utils.pause()
            elif c == "2":
                name = Prompt.ask("  Dateiname (oder Teil)")
                path = Prompt.ask("  Suchpfad", default="/")
                self.db.add_history("dateien", f"find {name} in {path}")
                Utils.run_live(f"find {path} -iname '*{name}*' 2>/dev/null | head -50")
                Utils.pause()
            elif c == "3":
                text = Prompt.ask("  Suchtext")
                path = Prompt.ask("  Suchpfad", default=".")
                self.db.add_history("dateien", f"grep {text} in {path}")
                Utils.run_live(f"grep -rn --color=auto '{text}' {path} 2>/dev/null | head -50")
                Utils.pause()
            elif c == "4":
                src = Prompt.ask("  Quelle")
                dst = Prompt.ask("  Ziel")
                self.db.add_history("dateien", f"cp {src} -> {dst}")
                Utils.run_live(f"cp -rv {src} {dst}")
                Utils.pause()
            elif c == "5":
                src = Prompt.ask("  Quelle")
                dst = Prompt.ask("  Ziel")
                self.db.add_history("dateien", f"mv {src} -> {dst}")
                Utils.run_live(f"mv -v {src} {dst}")
                Utils.pause()
            elif c == "6":
                path = Prompt.ask("  Pfad zum Loeschen")
                if Confirm.ask(f"  Wirklich loeschen: {path}?"):
                    self.db.add_history("dateien", f"rm {path}")
                    Utils.run_live(f"rm -rv {path}")
                Utils.pause()
            elif c == "7":
                path = Prompt.ask("  Datei/Ordner")
                mode = Prompt.ask("  Rechte (z.B. 755, u+x)")
                recursive = Confirm.ask("  Rekursiv?", default=False)
                flag = "-R" if recursive else ""
                self.db.add_history("dateien", f"chmod {mode} {path}")
                Utils.run_live(f"chmod {flag} {mode} {path}")
                Utils.pause()
            elif c == "8":
                path = Prompt.ask("  Datei/Ordner")
                owner = Prompt.ask("  Besitzer (user:group)")
                recursive = Confirm.ask("  Rekursiv?", default=False)
                flag = "-R" if recursive else ""
                self.db.add_history("dateien", f"chown {owner} {path}")
                Utils.run_live(f"sudo chown {flag} {owner} {path}")
                Utils.pause()
            elif c == "9":
                path = Prompt.ask("  Datei")
                self.db.add_history("dateien", f"info {path}")
                Utils.run_live(f"stat {path}")
                console.print()
                Utils.run_live(f"file {path}")
                Utils.pause()
            elif c == "10":
                path = Prompt.ask("  Suchpfad", default="/home")
                size = Prompt.ask("  Mindestgroesse (z.B. 100M)", default="100M")
                self.db.add_history("dateien", f"grosse Dateien in {path}")
                Utils.run_live(f"find {path} -type f -size +{size} -exec ls -lh {{}} + 2>/dev/null | sort -k5 -h | tail -20")
                Utils.pause()
            elif c == "11":
                path = Prompt.ask("  Suchpfad", default=".")
                self.db.add_history("dateien", f"Duplikate in {path}")
                console.print("  [dim]Suche nach gleicher Groesse...[/dim]")
                Utils.run_live(f"find {path} -type f -exec md5sum {{}} + 2>/dev/null | sort | uniq -d -w 32 | head -20")
                Utils.pause()
            elif c == "12":
                path = Prompt.ask("  Verzeichnis", default=".")
                self.db.add_history("dateien", f"Groesse {path}")
                Utils.run_live(f"du -sh {path}")
                console.print()
                Utils.run_live(f"du -h --max-depth=1 {path} 2>/dev/null | sort -h | tail -15")
                Utils.pause()
            elif c == "13":
                src = Prompt.ask("  Was sichern (Pfad)")
                dst = Prompt.ask("  Backup-Datei (z.B. /tmp/backup.tar.gz)")
                self.db.add_history("dateien", f"Backup {src} -> {dst}")
                Utils.run_live(f"tar -czvf {dst} {src}")
                console.print(f"  [green]Backup erstellt: {dst}[/green]")
                Utils.pause()
            elif c == "14":
                src = Prompt.ask("  Archiv-Datei")
                dst = Prompt.ask("  Entpacken nach", default=".")
                self.db.add_history("dateien", f"Entpacke {src}")
                Utils.run_live(f"tar -xzvf {src} -C {dst}")
                Utils.pause()
            elif c == "15":
                path = Prompt.ask("  Suchpfad", default=".")
                self.db.add_history("dateien", f"Leere in {path}")
                console.print("  [bold]Leere Dateien:[/bold]")
                Utils.run_live(f"find {path} -type f -empty 2>/dev/null | head -20")
                console.print("  [bold]Leere Ordner:[/bold]")
                Utils.run_live(f"find {path} -type d -empty 2>/dev/null | head -20")
                Utils.pause()
            elif c == "16":
                path = Prompt.ask("  Suchpfad", default=".")
                mins = Prompt.ask("  Geaendert in letzten X Minuten", default="60")
                self.db.add_history("dateien", f"Letzte Aenderungen in {path}")
                Utils.run_live(f"find {path} -type f -mmin -{mins} 2>/dev/null | head -30")
                Utils.pause()
