"""
FRED v2.0 - System Tools & Utilities
Datei-Ops, System-Info, Netzwerk, Rechner, Timer, Backup
"""

import os
import sys
import time
import json
import shutil
import socket
import subprocess
import platform
from datetime import datetime

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


def header(title="Tools"):
    width = os.get_terminal_size().columns
    print(f"\n{MAGENTA}{BOLD}{'═' * width}")
    print(f"  🔧 {title}")
    print(f"{'═' * width}{R}")


# ══════════════════════════════════════════
#  SYSTEM INFO
# ══════════════════════════════════════════

def system_info():
    clear()
    header("System Info")

    # OS
    uname = platform.uname()
    print(f"\n  {BOLD}🖥️  System:{R}")
    print(f"    OS:       {GREEN}{uname.system} {uname.release}{R}")
    print(f"    Host:     {uname.node}")
    print(f"    Arch:     {uname.machine}")
    print(f"    Python:   {platform.python_version()}")

    # CPU
    print(f"\n  {BOLD}⚡ CPU:{R}")
    try:
        with open('/proc/cpuinfo') as f:
            cpuinfo = f.read()
        model = [l for l in cpuinfo.split('\n') if 'model name' in l]
        if model:
            cpu_name = model[0].split(':')[1].strip()
            print(f"    Modell:   {cpu_name}")
        cores = os.cpu_count()
        print(f"    Kerne:    {cores}")
    except:
        print(f"    Kerne:    {os.cpu_count()}")

    # Uptime
    try:
        with open('/proc/uptime') as f:
            uptime_sec = float(f.read().split()[0])
        days = int(uptime_sec // 86400)
        hours = int((uptime_sec % 86400) // 3600)
        mins = int((uptime_sec % 3600) // 60)
        print(f"    Uptime:   {days}d {hours}h {mins}m")
    except:
        pass

    # RAM
    print(f"\n  {BOLD}💾 Speicher:{R}")
    try:
        with open('/proc/meminfo') as f:
            mem = f.read()
        total = int([l for l in mem.split('\n') if 'MemTotal' in l][0].split()[1]) // 1024
        avail = int([l for l in mem.split('\n') if 'MemAvailable' in l][0].split()[1]) // 1024
        used = total - avail
        pct = used / total * 100
        color = GREEN if pct < 60 else YELLOW if pct < 85 else RED
        bar_w = 20
        filled = int(bar_w * pct / 100)
        bar = f"{'█' * filled}{'░' * (bar_w - filled)}"
        print(f"    RAM:      {color}[{bar}] {pct:.0f}%{R}")
        print(f"              {used}MB / {total}MB")
    except:
        pass

    # Disk
    print(f"\n  {BOLD}💿 Festplatte:{R}")
    try:
        stat = shutil.disk_usage('/')
        total_gb = stat.total / (1024**3)
        used_gb = stat.used / (1024**3)
        free_gb = stat.free / (1024**3)
        pct = stat.used / stat.total * 100
        color = GREEN if pct < 60 else YELLOW if pct < 85 else RED
        filled = int(20 * pct / 100)
        bar = f"{'█' * filled}{'░' * (20 - filled)}"
        print(f"    Root:     {color}[{bar}] {pct:.0f}%{R}")
        print(f"              {used_gb:.1f}GB / {total_gb:.1f}GB ({free_gb:.1f}GB frei)")
    except:
        pass

    # Netzwerk
    print(f"\n  {BOLD}🌐 Netzwerk:{R}")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"    Hostname: {hostname}")
        print(f"    Lokal IP: {local_ip}")
    except:
        pass

    try:
        result = subprocess.run(['curl', '-s', '--max-time', '3', 'ifconfig.me'],
                                capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"    Extern:   {result.stdout.strip()}")
    except:
        pass

    # Temperatur (Raspberry Pi)
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp = int(f.read().strip()) / 1000
        color = GREEN if temp < 60 else YELLOW if temp < 75 else RED
        print(f"\n  {BOLD}🌡️  Temperatur:{R}")
        print(f"    CPU:      {color}{temp:.1f}°C{R}")
    except:
        pass

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  PROZESS MONITOR
# ══════════════════════════════════════════

def process_monitor():
    clear()
    header("Prozess Monitor")

    try:
        result = subprocess.run(
            ['ps', 'aux', '--sort=-%mem'],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')

        print(f"\n  {BOLD}Top 15 Prozesse (nach RAM):{R}\n")
        print(f"  {DIM}{'USER':<12} {'%CPU':>5} {'%MEM':>5}  {'COMMAND'}{R}")
        print(f"  {DIM}{'─' * 50}{R}")

        for line in lines[1:16]:
            parts = line.split()
            if len(parts) >= 11:
                user = parts[0][:11]
                cpu = parts[2]
                mem = parts[3]
                cmd = parts[10][:30]

                mem_f = float(mem)
                color = RED if mem_f > 10 else YELLOW if mem_f > 5 else ""
                end = R if color else ""

                print(f"  {color}{user:<12} {cpu:>5} {mem:>5}  {cmd}{end}")
    except Exception as e:
        print(f"  {RED}Fehler: {e}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  DATEI BROWSER
# ══════════════════════════════════════════

def file_browser():
    path = os.path.expanduser('~')

    while True:
        clear()
        header(f"Datei Browser")
        print(f"  {DIM}📂 {path}{R}\n")

        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            print(f"  {RED}Kein Zugriff!{R}")
            path = os.path.dirname(path)
            input(f"  {DIM}Enter...{R}")
            continue

        dirs = []
        files = []

        for item in items:
            full = os.path.join(path, item)
            if item.startswith('.'):
                continue
            if os.path.isdir(full):
                dirs.append(item)
            else:
                files.append(item)

        # Verzeichnisse
        for i, d in enumerate(dirs):
            print(f"  {YELLOW}[{i+1}]{R} 📁 {BOLD}{d}/{R}")

        # Dateien
        offset = len(dirs)
        for i, f_name in enumerate(files):
            full = os.path.join(path, f_name)
            size = os.path.getsize(full)
            if size > 1024*1024:
                size_str = f"{size/(1024*1024):.1f}MB"
            elif size > 1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size}B"

            ext = os.path.splitext(f_name)[1]
            emoji = "📄"
            if ext in ('.py', '.js', '.sh', '.c', '.rs', '.go'):
                emoji = "📝"
            elif ext in ('.jpg', '.png', '.gif', '.svg'):
                emoji = "🖼️"
            elif ext in ('.mp3', '.wav', '.flac'):
                emoji = "🎵"
            elif ext in ('.mp4', '.mkv', '.avi'):
                emoji = "🎬"
            elif ext in ('.zip', '.tar', '.gz'):
                emoji = "📦"
            elif ext in ('.md', '.txt', '.log'):
                emoji = "📃"

            print(f"  {YELLOW}[{offset+i+1}]{R} {emoji} {f_name} {DIM}({size_str}){R}")

        total = len(dirs) + len(files)
        print(f"\n  {DIM}{len(dirs)} Ordner, {len(files)} Dateien{R}")
        print(f"\n  {YELLOW}[..]{R} Überordner  {YELLOW}[cd]{R} Pfad eingeben")
        print(f"  {YELLOW}[v]{R}  Datei ansehen  {YELLOW}[0]{R} Zurück")

        choice = input(f"\n  {CYAN}▸{R} ").strip()

        if choice == "0":
            break
        elif choice == "..":
            path = os.path.dirname(path)
        elif choice == "cd":
            new_path = input(f"  {CYAN}Pfad:{R} ").strip()
            new_path = os.path.expanduser(new_path)
            if os.path.isdir(new_path):
                path = new_path
            else:
                print(f"  {RED}Ungültiger Pfad.{R}")
                input(f"  {DIM}Enter...{R}")
        elif choice == "v":
            fn = input(f"  {CYAN}Dateiname:{R} ").strip()
            view_file(os.path.join(path, fn))
        elif choice.isdigit():
            idx = int(choice) - 1
            all_items = dirs + files
            if 0 <= idx < len(all_items):
                selected = all_items[idx]
                full = os.path.join(path, selected)
                if os.path.isdir(full):
                    path = full
                else:
                    view_file(full)


def view_file(filepath):
    clear()
    header(f"Datei: {os.path.basename(filepath)}")

    if not os.path.exists(filepath):
        print(f"  {RED}Datei nicht gefunden.{R}")
        input(f"  {DIM}Enter...{R}")
        return

    size = os.path.getsize(filepath)
    if size > 100000:
        print(f"  {YELLOW}Datei zu groß ({size/1024:.1f}KB). Nur erste 100 Zeilen:{R}")

    print(f"  {DIM}Größe: {size} Bytes{R}\n")

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()[:100]
        for i, line in enumerate(lines, 1):
            print(f"  {DIM}{i:4}{R} │ {line.rstrip()}")
    except UnicodeDecodeError:
        print(f"  {YELLOW}Binärdatei - kann nicht angezeigt werden.{R}")
    except Exception as e:
        print(f"  {RED}Fehler: {e}{R}")

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  SCHNELL-RECHNER
# ══════════════════════════════════════════

def calculator():
    clear()
    header("Rechner")
    print(f"  {DIM}Mathematische Ausdrücke eingeben. 'q' zum Beenden.{R}")
    print(f"  {DIM}Erlaubt: +, -, *, /, **, (, ), sqrt(), abs(){R}")
    print(f"  {DIM}Variablen: ans = letztes Ergebnis{R}\n")

    import math
    safe_dict = {
        "sqrt": math.sqrt, "abs": abs, "pi": math.pi, "e": math.e,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "pow": pow,
        "round": round, "floor": math.floor, "ceil": math.ceil,
        "ans": 0
    }

    while True:
        expr = input(f"  {CYAN}▸{R} ").strip()
        if expr.lower() in ('q', 'quit', '0'):
            break
        if not expr:
            continue

        try:
            # Sicherheitscheck
            forbidden = ['import', 'exec', 'eval', 'open', '__', 'os', 'sys']
            if any(f in expr.lower() for f in forbidden):
                print(f"  {RED}Nicht erlaubt.{R}")
                continue

            result = eval(expr, {"__builtins__": {}}, safe_dict)
            safe_dict["ans"] = result
            print(f"  {GREEN}= {result}{R}\n")
        except ZeroDivisionError:
            print(f"  {RED}Division durch 0!{R}\n")
        except Exception as e:
            print(f"  {RED}Fehler: {e}{R}\n")


# ══════════════════════════════════════════
#  TIMER & STOPPUHR
# ══════════════════════════════════════════

def timer_menu():
    clear()
    header("Timer & Stoppuhr")
    print(f"\n  {YELLOW}[1]{R} ⏱️  Stoppuhr")
    print(f"  {YELLOW}[2]{R} ⏲️  Countdown Timer")
    print(f"  {YELLOW}[3]{R} 🍅 Pomodoro (25/5)")
    print(f"  {YELLOW}[0]{R} Zurück")

    choice = input(f"\n  {CYAN}▸{R} ").strip()

    if choice == "1":
        stopwatch()
    elif choice == "2":
        countdown()
    elif choice == "3":
        pomodoro()


def stopwatch():
    clear()
    print(f"\n  {CYAN}⏱️  Stoppuhr{R}")
    print(f"  {DIM}Enter = Start/Stopp/Runde | q = Beenden{R}\n")

    input(f"  {CYAN}Enter zum Starten...{R}")
    start = time.time()
    laps = []

    while True:
        inp = input(f"  {YELLOW}Enter=Runde | q=Stopp:{R} ").strip().lower()
        elapsed = time.time() - start

        if inp == 'q':
            print(f"\n  {GREEN}⏱️  Gesamt: {elapsed:.2f}s{R}")
            if laps:
                print(f"  {DIM}Runden:{R}")
                for i, l in enumerate(laps, 1):
                    print(f"    {i}. {l:.2f}s")
            break
        else:
            laps.append(elapsed)
            print(f"  {GREEN}Runde {len(laps)}: {elapsed:.2f}s{R}")

    input(f"\n  {DIM}Enter...{R}")


def countdown():
    mins = input(f"\n  {CYAN}Minuten:{R} ").strip()
    try:
        total = int(mins) * 60
    except:
        total = 60

    print(f"\n  {CYAN}⏲️  Countdown: {mins} Minuten{R}\n")

    start = time.time()
    try:
        while True:
            elapsed = time.time() - start
            remaining = max(0, total - elapsed)
            m = int(remaining // 60)
            s = int(remaining % 60)
            bar_w = 30
            pct = elapsed / total if total > 0 else 1
            filled = int(bar_w * pct)
            bar = f"{'█' * filled}{'░' * (bar_w - filled)}"
            print(f"\r  [{bar}] {m:02d}:{s:02d}  ", end='', flush=True)

            if remaining <= 0:
                print(f"\n\n  {GREEN}{BOLD}🔔 ZEIT UM!{R}")
                # Beep
                print('\a', end='', flush=True)
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        elapsed = time.time() - start
        print(f"\n\n  {YELLOW}Abgebrochen nach {elapsed:.0f}s{R}")

    input(f"\n  {DIM}Enter...{R}")


def pomodoro():
    clear()
    print(f"\n  {RED}🍅 Pomodoro Timer{R}")
    print(f"  {DIM}25 Min Arbeit → 5 Min Pause{R}\n")

    sessions = input(f"  {CYAN}Wie viele Sessions? (4):{R} ").strip()
    sessions = int(sessions) if sessions.isdigit() else 4

    for s in range(1, sessions + 1):
        print(f"\n  {RED}🍅 Session {s}/{sessions} - ARBEITSZEIT (25 Min){R}")
        input(f"  {CYAN}Enter zum Starten...{R}")

        try:
            run_timer(25 * 60, "ARBEIT")
        except KeyboardInterrupt:
            print(f"\n  {YELLOW}Abgebrochen.{R}")
            input(f"  {DIM}Enter...{R}")
            return

        print(f"\n  {GREEN}{BOLD}🔔 PAUSE! (5 Min){R}")
        print('\a', end='', flush=True)

        if s < sessions:
            input(f"  {CYAN}Enter für Pause...{R}")
            try:
                run_timer(5 * 60, "PAUSE")
            except KeyboardInterrupt:
                pass

    print(f"\n  {GREEN}{BOLD}🎉 Alle {sessions} Sessions geschafft!{R}")
    input(f"\n  {DIM}Enter...{R}")


def run_timer(total_sec, label=""):
    start = time.time()
    while True:
        elapsed = time.time() - start
        remaining = max(0, total_sec - elapsed)
        m = int(remaining // 60)
        s = int(remaining % 60)
        pct = elapsed / total_sec
        bar_w = 25
        filled = int(bar_w * pct)
        bar = f"{'█' * filled}{'░' * (bar_w - filled)}"
        print(f"\r  {label} [{bar}] {m:02d}:{s:02d}  ", end='', flush=True)
        if remaining <= 0:
            print()
            break
        time.sleep(0.5)


# ══════════════════════════════════════════
#  NETZWERK TOOLS
# ══════════════════════════════════════════

def network_tools():
    clear()
    header("Netzwerk Tools")
    print(f"\n  {YELLOW}[1]{R} 🏓 Ping")
    print(f"  {YELLOW}[2]{R} 🔍 DNS Lookup")
    print(f"  {YELLOW}[3]{R} 🌐 Port Check")
    print(f"  {YELLOW}[4]{R} 📡 Speedtest (einfach)")
    print(f"  {YELLOW}[5]{R} 📶 WLAN Info")
    print(f"  {YELLOW}[0]{R} Zurück")

    choice = input(f"\n  {CYAN}▸{R} ").strip()

    if choice == "1":
        host = input(f"\n  {CYAN}Host/IP:{R} ").strip() or "8.8.8.8"
        print(f"\n  {DIM}Ping {host}...{R}\n")
        os.system(f'ping -c 4 {host}')
        input(f"\n  {DIM}Enter...{R}")

    elif choice == "2":
        domain = input(f"\n  {CYAN}Domain:{R} ").strip()
        if domain:
            try:
                ip = socket.gethostbyname(domain)
                print(f"\n  {GREEN}{domain} → {ip}{R}")
            except:
                print(f"\n  {RED}Nicht gefunden.{R}")
        input(f"\n  {DIM}Enter...{R}")

    elif choice == "3":
        host = input(f"\n  {CYAN}Host:{R} ").strip()
        port = input(f"  {CYAN}Port:{R} ").strip()
        if host and port.isdigit():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, int(port)))
                sock.close()
                if result == 0:
                    print(f"\n  {GREEN}✅ Port {port} ist OFFEN{R}")
                else:
                    print(f"\n  {RED}❌ Port {port} ist GESCHLOSSEN{R}")
            except Exception as e:
                print(f"\n  {RED}Fehler: {e}{R}")
        input(f"\n  {DIM}Enter...{R}")

    elif choice == "4":
        print(f"\n  {CYAN}📡 Download-Test...{R}")
        try:
            start = time.time()
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{size_download}',
                 '--max-time', '10', 'http://speedtest.tele2.net/1MB.zip'],
                capture_output=True, text=True
            )
            elapsed = time.time() - start
            size = int(result.stdout) if result.stdout.isdigit() else 0
            if elapsed > 0 and size > 0:
                speed = (size / elapsed) / (1024 * 1024) * 8
                print(f"  {GREEN}⬇️  ~{speed:.1f} Mbit/s{R}")
                print(f"  {DIM}({size/1024:.0f}KB in {elapsed:.1f}s){R}")
            else:
                print(f"  {RED}Test fehlgeschlagen.{R}")
        except Exception as e:
            print(f"  {RED}Fehler: {e}{R}")
        input(f"\n  {DIM}Enter...{R}")

    elif choice == "5":
        print(f"\n  {CYAN}📶 WLAN Info:{R}\n")
        os.system('iwconfig 2>/dev/null || echo "  Kein WLAN gefunden"')
        print()
        os.system('ip addr show 2>/dev/null | grep -E "inet |wlan|eth"')
        input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  BACKUP
# ══════════════════════════════════════════

def backup_tool():
    clear()
    header("Backup")

    fred_dir = os.path.expanduser('~/fred')
    backup_dir = os.path.expanduser('~/fred_backups')

    print(f"\n  {YELLOW}[1]{R} 💾 Fred Backup erstellen")
    print(f"  {YELLOW}[2]{R} 📂 Backups anzeigen")
    print(f"  {YELLOW}[3]{R} ♻️  Backup wiederherstellen")
    print(f"  {YELLOW}[0]{R} Zurück")

    choice = input(f"\n  {CYAN}▸{R} ").strip()

    if choice == "1":
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"fred_backup_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)

        print(f"\n  {CYAN}💾 Erstelle Backup...{R}")

        try:
            shutil.copytree(fred_dir, backup_path,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            # Größe berechnen
            total_size = 0
            file_count = 0
            for dirpath, dirnames, filenames in os.walk(backup_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
                    file_count += 1

            print(f"  {GREEN}✅ Backup erstellt!{R}")
            print(f"  {DIM}Pfad:    {backup_path}{R}")
            print(f"  {DIM}Dateien: {file_count}{R}")
            print(f"  {DIM}Größe:   {total_size/1024:.1f}KB{R}")
        except Exception as e:
            print(f"  {RED}Fehler: {e}{R}")

        input(f"\n  {DIM}Enter...{R}")

    elif choice == "2":
        if not os.path.exists(backup_dir):
            print(f"\n  {DIM}Keine Backups vorhanden.{R}")
        else:
            backups = sorted(os.listdir(backup_dir), reverse=True)
            if not backups:
                print(f"\n  {DIM}Keine Backups vorhanden.{R}")
            else:
                print(f"\n  {BOLD}Vorhandene Backups:{R}\n")
                for i, b in enumerate(backups, 1):
                    bp = os.path.join(backup_dir, b)
                    size = sum(
                        os.path.getsize(os.path.join(dp, f))
                        for dp, dn, fn in os.walk(bp) for f in fn
                    ) if os.path.isdir(bp) else 0
                    print(f"  {YELLOW}[{i}]{R} 📦 {b} {DIM}({size/1024:.1f}KB){R}")

        input(f"\n  {DIM}Enter...{R}")

    elif choice == "3":
        if not os.path.exists(backup_dir):
            print(f"\n  {RED}Keine Backups vorhanden.{R}")
            input(f"  {DIM}Enter...{R}")
            return

        backups = sorted(os.listdir(backup_dir), reverse=True)
        if not backups:
            print(f"\n  {RED}Keine Backups.{R}")
            input(f"  {DIM}Enter...{R}")
            return

        for i, b in enumerate(backups, 1):
            print(f"  {YELLOW}[{i}]{R} {b}")

        sel = input(f"\n  {CYAN}Backup Nr:{R} ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(backups):
            backup_path = os.path.join(backup_dir, backups[int(sel) - 1])
            confirm = input(f"  {RED}⚠️  Fred-Ordner überschreiben? (ja):{R} ").strip().lower()
            if confirm == "ja":
                try:
                    # Aktuelle .py Dateien sichern
                    for f in os.listdir(backup_path):
                        src = os.path.join(backup_path, f)
                        dst = os.path.join(fred_dir, f)
                        if os.path.isfile(src):
                            shutil.copy2(src, dst)
                    print(f"  {GREEN}✅ Wiederhergestellt!{R}")
                except Exception as e:
                    print(f"  {RED}Fehler: {e}{R}")

        input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  QUICK SHELL
# ══════════════════════════════════════════

def quick_shell():
    clear()
    header("Quick Shell")
    print(f"  {DIM}Shell-Befehle direkt ausführen. 'exit' zum Beenden.{R}")
    print(f"  {DIM}⚠️  Vorsicht bei destruktiven Befehlen!{R}\n")

    blocked = ['rm -rf /', 'mkfs', ':(){', 'dd if=/dev/zero']

    while True:
        cmd = input(f"  {GREEN}${R} ").strip()

        if cmd.lower() in ('exit', 'quit', 'q', '0'):
            break
        if not cmd:
            continue

        # Sicherheitscheck
        if any(b in cmd for b in blocked):
            print(f"  {RED}⛔ Blockiert aus Sicherheitsgründen!{R}")
            continue

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                for line in result.stdout.rstrip().split('\n'):
                    print(f"  {line}")
            if result.stderr:
                for line in result.stderr.rstrip().split('\n'):
                    print(f"  {RED}{line}{R}")
        except subprocess.TimeoutExpired:
            print(f"  {RED}Timeout (30s)!{R}")
        except Exception as e:
            print(f"  {RED}Fehler: {e}{R}")
        print()


# ══════════════════════════════════════════
#  PASSWORT GENERATOR
# ══════════════════════════════════════════

def password_generator():
    clear()
    header("Passwort Generator")

    import string
    import secrets

    length = input(f"\n  {CYAN}Länge (16):{R} ").strip()
    length = int(length) if length.isdigit() else 16

    print(f"\n  {BOLD}Generierte Passwörter:{R}\n")

    charsets = [
        ("Stark",    string.ascii_letters + string.digits + "!@#$%&*"),
        ("Alphanum", string.ascii_letters + string.digits),
        ("PIN",      string.digits),
        ("Hex",      string.hexdigits[:16]),
    ]

    for name, chars in charsets:
        pw = ''.join(secrets.choice(chars) for _ in range(length))
        print(f"  {CYAN}{name:>8}:{R} {GREEN}{pw}{R}")

    # Passphrase
    try:
        with open('/usr/share/dict/words', 'r') as f:
            words = [w.strip().lower() for w in f if 4 <= len(w.strip()) <= 8]
        if words:
            phrase = '-'.join(secrets.choice(words) for _ in range(4))
            print(f"  {CYAN}{'Phrase':>8}:{R} {GREEN}{phrase}{R}")
    except:
        pass

    input(f"\n  {DIM}Enter...{R}")


# ══════════════════════════════════════════
#  HAUPTMENÜ
# ══════════════════════════════════════════

def tools_menu():
    while True:
        clear()
        header("System Tools")

        print(f"""
  {YELLOW}[1]{R} 🖥️  System Info          {YELLOW}[2]{R} 📊 Prozess Monitor
  {YELLOW}[3]{R} 📂 Datei Browser        {YELLOW}[4]{R} 🧮 Rechner
  {YELLOW}[5]{R} ⏱️  Timer & Stoppuhr     {YELLOW}[6]{R} 🌐 Netzwerk Tools
  {YELLOW}[7]{R} 💾 Backup               {YELLOW}[8]{R} 💻 Quick Shell
  {YELLOW}[9]{R} 🔑 Passwort Generator

  {YELLOW}[0]{R} Zurück
        """)

        choice = input(f"  {CYAN}▸{R} ").strip()

        if choice == "1":
            system_info()
        elif choice == "2":
            process_monitor()
        elif choice == "3":
            file_browser()
        elif choice == "4":
            calculator()
        elif choice == "5":
            timer_menu()
        elif choice == "6":
            network_tools()
        elif choice == "7":
            backup_tool()
        elif choice == "8":
            quick_shell()
        elif choice == "9":
            password_generator()
        elif choice == "0":
            break


# ══════════════════════════════════════════
#  SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    print(f"{MAGENTA}{BOLD}🔧 Fred System Tools{R}")
    print(f"{'=' * 40}")

    print(f"\n  Tools verfügbar:")
    tools = [
        "🖥️  System Info", "📊 Prozess Monitor", "📂 Datei Browser",
        "🧮 Rechner", "⏱️  Timer & Stoppuhr", "🌐 Netzwerk Tools",
        "💾 Backup", "💻 Quick Shell", "🔑 Passwort Generator"
    ]
    for t in tools:
        print(f"    • {t}")

    print(f"\n  System: {platform.system()} {platform.release()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  CPU:    {os.cpu_count()} Kerne")

    stat = shutil.disk_usage('/')
    free_gb = stat.free / (1024**3)
    print(f"  Disk:   {free_gb:.1f}GB frei")

    print(f"\n  ✅ fred_tools.py geladen!")
