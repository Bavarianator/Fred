"""
FRED v5.0 - Main Menu / Hauptmenü
Unites: Chat System, Tools, Settings
Vereint: Chat-System, Tools, Einstellungen
"""

import os
import sys

# Import language module / Sprachmodul importieren
try:
    from fred_lang import t, lang
except ImportError:
    # Fallback if module doesn't exist yet
    def t(key, **kwargs):
        return f"[{key}]"
    class FakeLang:
        current_lang = "de"
        def get_current_code(self): return "de"
        def set_language(self, l): pass
    lang = FakeLang()

CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
R = "\033[0m"


def clear():
    os.system('clear')


def banner():
    width = os.get_terminal_size().columns
    print(f"""
{CYAN}{BOLD}{'═' * width}
  ███████╗██████╗ ███████╗██████╗
  ██╔════╝██╔══██╗██╔════╝██╔══██╗
  █████╗  ██████╔╝█████╗  ██║  ██║
  ██╔══╝  ██╔══██╗██╔══╝  ██║  ██║
  ██║     ██║  ██║███████╗██████╔╝
  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝  v5.0
{'═' * width}{R}""")


def show_provider():
    """Shows current provider in status line / Zeigt aktuellen Provider in Statuszeile"""
    try:
        from fred_settings import get_provider, get_model, PROVIDERS
        p = get_provider()
        m = get_model()
        name = PROVIDERS.get(p, {}).get("name", p)
        print(f"  {DIM}📡 {name} / {m}{R}\n")
    except:
        print(f"  {DIM}📡 Not configured / Nicht konfiguriert{R}\n")


def main():
    while True:
        clear()
        banner()
        show_provider()

        # AI Chat Section
        print(f"  {CYAN}{BOLD}── {t('menu_chat').split('. ')[1] if '. ' in t('menu_chat') else 'AI Chat'} ──{R}")
        print(f"  {YELLOW}1{R}  💬 {t('menu_chat').split('. ')[1] if '. ' in t('menu_chat') else 'New Chat'}")
        print(f"  {YELLOW}2{R}  📚 Chat History / Chat-Verlauf")
        print(f"  {YELLOW}3{R}  ⚡ Quick Question / Schnelle Frage")
        print()
        
        # Tools Section
        print(f"  {CYAN}{BOLD}── Tools ──{R}")
        print(f"  {YELLOW}4{R}  📁 File Manager / Datei-Manager")
        print(f"  {YELLOW}5{R}  🌐 Network Tools / Netzwerk-Tools")
        print(f"  {YELLOW}6{R}  🖥  System Tools / System-Tools")
        print(f"  {YELLOW}7{R}  📝 Notes & Projects / Notizen & Projekte")
        print(f"  {YELLOW}8{R}  🤖 AI Coder")
        print()
        
        # System Section
        print(f"  {CYAN}{BOLD}── System ──{R}")
        print(f"  {YELLOW}9{R}  ⚙️  Settings / Einstellungen")
        print(f"  {YELLOW}L{R}  🌐 Language / Sprache ({lang.get_current_code().upper()})")
        print(f"  {YELLOW}0{R}  🚪 {t('menu_exit').split('. ')[1] if '. ' in t('menu_exit') else 'Exit'}")

        print()
        choice = input(f"  {CYAN}FRED ▸{R} ").strip().lower()

        # Language switch / Sprachumschaltung
        if choice == "l":
            new_lang = "en" if lang.get_current_code() == "de" else "de"
            lang.set_language(new_lang)
            continue

        # ── AI Chat ──
        if choice == "1":
            try:
                from fred_chat import new_chat
                new_chat()
            except Exception as e:
                print(f"  {RED}❌ {e}{R}")
                input(f"\n  {DIM}Enter...{R}")

        elif choice == "2":
            try:
                from fred_chat import chat_history
                chat_history()
            except Exception as e:
                print(f"  {RED}❌ {e}{R}")
                input(f"\n  {DIM}Enter...{R}")

        elif choice == "3":
            try:
                from fred_chat import quick_question
                quick_question()
            except Exception as e:
                print(f"  {RED}❌ {e}{R}")
                input(f"\n  {DIM}Enter...{R}")

        # ── Tools ──
        elif choice == "4":
            _run_module("fred_files", "FileManager")

        elif choice == "5":
            _run_module("fred_network", "NetworkTools")

        elif choice == "6":
            _run_module("fred_system", "SystemTools")

        elif choice == "7":
            _run_submenu_notes()

        elif choice == "8":
            try:
                from fred_coder import coder_menu
                coder_menu()
            except ImportError:
                print(f"  {RED}❌ fred_coder.py not found / nicht gefunden{R}")
                input(f"\n  {DIM}Enter...{R}")
            except Exception as e:
                print(f"  {RED}❌ {e}{R}")
                input(f"\n  {DIM}Enter...{R}")

        # ── System ──
        elif choice == "9":
            try:
                from fred_settings import settings_menu
                settings_menu()
            except Exception as e:
                print(f"  {RED}❌ {e}{R}")
                input(f"\n  {DIM}Enter...{R}")

        elif choice == "0":
            print(f"\n  {CYAN}Goodbye! / Auf Wiedersehen! 👋{R}\n")
            sys.exit(0)


def _run_module(module_name, class_name):
    """Versucht altes Modul zu laden (v5 Kompatibilität)"""
    try:
        mod = __import__(module_name)
        cls = getattr(mod, class_name, None)
        if cls:
            # Altes System brauchte FredDB - wir faken es
            try:
                from fred_db import FredDB
                db = FredDB()
            except:
                db = None
            obj = cls(db)
            obj.menu()
        else:
            print(f"  {RED}❌ {class_name} nicht in {module_name}{R}")
            input(f"\n  {DIM}Enter...{R}")
    except ImportError:
        print(f"  {RED}❌ {module_name}.py nicht gefunden{R}")
        input(f"\n  {DIM}Enter...{R}")
    except Exception as e:
        print(f"  {RED}❌ {e}{R}")
        input(f"\n  {DIM}Enter...{R}")


def _run_submenu_notes():
    """Notizen & Projekte Untermenü"""
    while True:
        clear()
        print(f"\n{CYAN}{BOLD}  📝 Notizen & Projekte{R}\n")
        print(f"  {YELLOW}1{R}  📝 Notizen")
        print(f"  {YELLOW}2{R}  📋 Projekte")
        print(f"  {YELLOW}0{R}  ← Zurück")
        
        c = input(f"\n  {CYAN}▸{R} ").strip()
        if c == "1":
            try:
                from fred_notes import notes_menu
                notes_menu()
            except ImportError:
                print(f"  {RED}❌ fred_notes.py nicht gefunden{R}")
                input(f"\n  {DIM}Enter...{R}")
            except Exception as e:
                print(f"  {RED}❌ {e}{R}")
                input(f"\n  {DIM}Enter...{R}")
        elif c == "2":
            try:
                from fred_projects import projects_menu
                projects_menu()
            except ImportError:
                print(f"  {RED}❌ fred_projects.py nicht gefunden{R}")
                input(f"\n  {DIM}Enter...{R}")
            except Exception as e:
                print(f"  {RED}❌ {e}{R}")
                input(f"\n  {DIM}Enter...{R}")
        elif c == "0":
            break


if __name__ == "__main__":
    main()
