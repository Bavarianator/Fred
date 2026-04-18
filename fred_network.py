#!/usr/bin/env python3
"""FRED v5.0 - Netzwerk-Modul"""

import os
import time
from fred_core import FredDB, Utils, console

try:
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.table import Table
    from rich import box
except ImportError:
    pass


class NetworkTools:
    def __init__(self, db: FredDB):
        self.db = db

    def menu(self):
        while True:
            console.clear()
            console.print("\n  [bold cyan]== Netzwerk ==[/bold cyan]\n")
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            table.add_column(style="bold yellow", width=4)
            table.add_column(style="white")
            table.add_row("1", "IP-Adressen anzeigen")
            table.add_row("2", "Ping")
            table.add_row("3", "Traceroute")
            table.add_row("4", "DNS Lookup")
            table.add_row("5", "Port-Scan (einfach)")
            table.add_row("6", "Offene Ports lokal")
            table.add_row("7", "Netzwerk-Interfaces")
            table.add_row("8", "ARP-Tabelle")
            table.add_row("9", "Speed-Test")
            table.add_row("10", "WiFi-Netzwerke scannen")
            table.add_row("11", "Netzwerk-Verbindungen")
            table.add_row("12", "Whois")
            table.add_row("13", "Route anzeigen")
            table.add_row("14", "Bandbreite live (iftop)")
            table.add_row("0", "Zurueck")
            console.print(table)

            c = Prompt.ask("  Netzwerk", default="0")

            if c == "0":
                return
            elif c == "1":
                self.db.add_history("netzwerk", "IP-Adressen")
                Utils.run_live("ip -c addr")
                Utils.pause()
            elif c == "2":
                host = Prompt.ask("  Ziel")
                count = Prompt.ask("  Anzahl Pings", default="4")
                self.db.add_history("netzwerk", f"Ping {host}")
                Utils.run_live(f"ping -c {count} {host}")
                Utils.pause()
            elif c == "3":
                host = Prompt.ask("  Ziel")
                self.db.add_history("netzwerk", f"Traceroute {host}")
                Utils.run_live(f"traceroute {host} 2>/dev/null || tracepath {host}")
                Utils.pause()
            elif c == "4":
                host = Prompt.ask("  Domain")
                self.db.add_history("netzwerk", f"DNS {host}")
                Utils.run_live(f"nslookup {host}")
                console.print()
                Utils.run_live(f"dig {host} +short 2>/dev/null")
                Utils.pause()
            elif c == "5":
                host = Prompt.ask("  Ziel-IP/Host")
                ports = Prompt.ask("  Ports (z.B. 22,80,443 oder 1-1024)", default="22,80,443,8080,8443,3306,5432")
                self.db.add_history("netzwerk", f"Portscan {host}")
                # Einfacher Bash-Scan
                if "-" in ports:
                    start, end = ports.split("-")
                    cmd = f'for p in $(seq {start} {end}); do (echo >/dev/tcp/{host}/$p) 2>/dev/null && echo "  Port $p: OFFEN"; done'
                    Utils.run_live(f"bash -c '{cmd}'")
                else:
                    for port in ports.split(","):
                        port = port.strip()
                        cmd = f'(echo >/dev/tcp/{host}/{port}) 2>/dev/null && echo "  Port {port}: OFFEN" || echo "  Port {port}: geschlossen"'
                        Utils.run_live(f"bash -c '{cmd}'")
                Utils.pause()
            elif c == "6":
                self.db.add_history("netzwerk", "Offene Ports lokal")
                Utils.run_live("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null")
                Utils.pause()
            elif c == "7":
                self.db.add_history("netzwerk", "Interfaces")
                Utils.run_live("ip -c link show")
                Utils.pause()
            elif c == "8":
                self.db.add_history("netzwerk", "ARP")
                Utils.run_live("ip neigh show")
                Utils.pause()
            elif c == "9":
                self.db.add_history("netzwerk", "Speedtest")
                console.print("  [dim]Braucht: sudo apt install speedtest-cli[/dim]")
                Utils.run_live("speedtest-cli --simple 2>/dev/null || echo 'speedtest-cli nicht installiert'")
                Utils.pause()
            elif c == "10":
                self.db.add_history("netzwerk", "WiFi-Scan")
                Utils.run_live("nmcli dev wifi list 2>/dev/null || sudo iwlist scan 2>/dev/null | grep -E 'ESSID|Quality' || echo 'Kein WiFi-Tool gefunden'")
                Utils.pause()
            elif c == "11":
                self.db.add_history("netzwerk", "Verbindungen")
                Utils.run_live("ss -tupn 2>/dev/null || netstat -tupn 2>/dev/null")
                Utils.pause()
            elif c == "12":
                domain = Prompt.ask("  Domain/IP")
                self.db.add_history("netzwerk", f"Whois {domain}")
                Utils.run_live(f"whois {domain} 2>/dev/null | head -40 || echo 'whois nicht installiert: sudo apt install whois'")
                Utils.pause()
            elif c == "13":
                self.db.add_history("netzwerk", "Route")
                Utils.run_live("ip route show")
                Utils.pause()
            elif c == "14":
                self.db.add_history("netzwerk", "iftop")
                console.print("  [dim]Strg+C zum Beenden. Braucht: sudo apt install iftop[/dim]")
                Utils.run_live("sudo iftop -t -s 10 2>/dev/null || echo 'iftop nicht installiert'")
                Utils.pause()
