#!/usr/bin/env python3
"""FRED v5.0 - System-Modul"""

import os
import time
from fred_core import FredDB, Utils, console

try:
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.table import Table
    from rich import box
except ImportError:
    pass


class SystemTools:
    def __init__(self, db: FredDB):
        self.db = db

    def menu(self):
        while True:
            console.clear()
            console.print("\n  [bold cyan]== System ==[/bold cyan]\n")
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            table.add_column(style="bold yellow", width=4)
            table.add_column(style="white")
            table.add_row("1", "System-Info")
            table.add_row("2", "CPU-Info")
            table.add_row("3", "RAM / Speicher")
            table.add_row("4", "Festplatten / Partitionen")
            table.add_row("5", "Prozesse (Top 20 CPU)")
            table.add_row("6", "Prozesse (Top 20 RAM)")
            table.add_row("7", "Prozess suchen")
            table.add_row("8", "Prozess beenden")
            table.add_row("9", "Services verwalten")
            table.add_row("10", "Temperatur")
            table.add_row("11", "Live-Monitor (CPU/RAM/Disk)")
            table.add_row("12", "Disk I/O")
            table.add_row("13", "Eingeloggte User")
            table.add_row("14", "Uptime / Lastverteilung")
            table.add_row("15", "Kernel / OS Info")
            table.add_row("16", "USB-Geraete")
            table.add_row("17", "PCI-Geraete")
            table.add_row("18", "Installierte Pakete zaehlen")
            table.add_row("0", "Zurueck")
            console.print(table)

            c = Prompt.ask("  System", default="0")

            if c == "0":
                return
            elif c == "1":
                self.db.add_history("system", "System-Info")
                Utils.run_live("hostnamectl 2>/dev/null || uname -a")
                Utils.pause()
            elif c == "2":
                self.db.add_history("system", "CPU-Info")
                Utils.run_live("lscpu | head -20")
                Utils.pause()
            elif c == "3":
                self.db.add_history("system", "RAM")
                Utils.run_live("free -h")
                console.print()
                Utils.run_live("swapon --show 2>/dev/null")
                Utils.pause()
            elif c == "4":
                self.db.add_history("system", "Festplatten")
                Utils.run_live("df -h")
                console.print()
                Utils.run_live("lsblk")
                Utils.pause()
            elif c == "5":
                self.db.add_history("system", "Top CPU")
                Utils.run_live("ps aux --sort=-%cpu | head -21")
                Utils.pause()
            elif c == "6":
                self.db.add_history("system", "Top RAM")
                Utils.run_live("ps aux --sort=-%mem | head -21")
                Utils.pause()
            elif c == "7":
                name = Prompt.ask("  Prozessname")
                self.db.add_history("system", f"Prozess suchen: {name}")
                Utils.run_live(f"ps aux | grep -i {name} | grep -v grep")
                Utils.pause()
            elif c == "8":
                pid = Prompt.ask("  PID zum Beenden")
                signal = Prompt.ask("  Signal (15=normal, 9=force)", default="15")
                self.db.add_history("system", f"Kill PID {pid}")
                Utils.run_live(f"kill -{signal} {pid}")
                console.print(f"  Signal {signal} an PID {pid} gesendet")
                Utils.pause()
            elif c == "9":
                self.service_menu()
            elif c == "10":
                self.db.add_history("system", "Temperatur")
                Utils.run_live("sensors 2>/dev/null || echo 'lm-sensors fehlt: sudo apt install lm-sensors'")
                Utils.pause()
            elif c == "11":
                self.db.add_history("system", "Live-Monitor")
                console.print("  [dim]Strg+C zum Beenden[/dim]\n")
                try:
                    while True:
                        load, _, _ = Utils.run("cat /proc/loadavg | awk '{print $1}'")
                        ram, _, _ = Utils.run("free | awk '/Mem:/ {printf \"%.1f%%\", $3/$2*100}'")
                        disk, _, _ = Utils.run("df / | awk 'NR==2 {print $5}'")
                        console.print(f"  Load: {load.strip():6s}  |  RAM: {ram.strip():6s}  |  Disk: {disk.strip()}", end="\r")
                        time.sleep(2)
                except KeyboardInterrupt:
                    console.print()
                Utils.pause()
            elif c == "12":
                self.db.add_history("system", "Disk I/O")
                Utils.run_live("iostat 2>/dev/null || echo 'sysstat fehlt: sudo apt install sysstat'")
                Utils.pause()
            elif c == "13":
                self.db.add_history("system", "User")
                Utils.run_live("w")
                Utils.pause()
            elif c == "14":
                self.db.add_history("system", "Uptime")
                Utils.run_live("uptime")
                Utils.pause()
            elif c == "15":
                self.db.add_history("system", "Kernel")
                Utils.run_live("uname -a")
                console.print()
                Utils.run_live("cat /etc/os-release 2>/dev/null")
                Utils.pause()
            elif c == "16":
                self.db.add_history("system", "USB")
                Utils.run_live("lsusb")
                Utils.pause()
            elif c == "17":
                self.db.add_history("system", "PCI")
                Utils.run_live("lspci")
                Utils.pause()
            elif c == "18":
                self.db.add_history("system", "Pakete")
                Utils.run_live("dpkg --list 2>/dev/null | wc -l && echo 'Pakete installiert (dpkg)'")
                Utils.pause()

    def service_menu(self):
        while True:
            console.clear()
            console.print("\n  [bold cyan]== Services ==[/bold cyan]\n")
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            table.add_column(style="bold yellow", width=4)
            table.add_column(style="white")
            table.add_row("1", "Alle aktiven Services")
            table.add_row("2", "Service-Status pruefen")
            table.add_row("3", "Service starten")
            table.add_row("4", "Service stoppen")
            table.add_row("5", "Service neustarten")
            table.add_row("6", "Fehlgeschlagene Services")
            table.add_row("0", "Zurueck")
            console.print(table)

            c = Prompt.ask("  Service", default="0")

            if c == "0":
                return
            elif c == "1":
                Utils.run_live("systemctl list-units --type=service --state=running --no-pager")
                Utils.pause()
            elif c == "2":
                name = Prompt.ask("  Service-Name")
                Utils.run_live(f"systemctl status {name} --no-pager -l")
                Utils.pause()
            elif c == "3":
                name = Prompt.ask("  Service-Name")
                Utils.run_live(f"sudo systemctl start {name}")
                Utils.run_live(f"systemctl status {name} --no-pager -l")
                Utils.pause()
            elif c == "4":
                name = Prompt.ask("  Service-Name")
                Utils.run_live(f"sudo systemctl stop {name}")
                console.print(f"  {name} gestoppt")
                Utils.pause()
            elif c == "5":
                name = Prompt.ask("  Service-Name")
                Utils.run_live(f"sudo systemctl restart {name}")
                Utils.run_live(f"systemctl status {name} --no-pager -l")
                Utils.pause()
            elif c == "6":
                Utils.run_live("systemctl list-units --type=service --state=failed --no-pager")
                Utils.pause()
