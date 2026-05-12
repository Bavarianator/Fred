"""
Fred Language Module / Fred Sprachmodul
Provides translations for German (de) and English (en).
Bietet Übersetzungen für Deutsch (de) und Englisch (en).
"""

TRANSLATIONS = {
    "de": {
        # General / Allgemein
        "welcome": "Willkommen bei Fred!",
        "goodbye": "Auf Wiedersehen!",
        "exit_prompt": "Beenden (exit/quit)?",
        "invalid_choice": "Ungültige Auswahl. Bitte versuchen Sie es erneut.",
        "loading": "Lade...",
        "error": "Fehler",
        "success": "Erfolg",
        "confirm": "Bestätigen",
        "cancel": "Abbrechen",
        
        # Menu / Menü
        "main_menu": "--- HAUPTMENÜ ---",
        "menu_chat": "1. Chat starten",
        "menu_coder": "2. Coder Modus",
        "menu_notes": "3. Notizen verwalten",
        "menu_projects": "4. Projekte verwalten",
        "menu_files": "5. Dateien durchsuchen",
        "menu_settings": "6. Einstellungen",
        "menu_exit": "0. Beenden",
        "select_option": "Wählen Sie eine Option",
        
        # Chat / Plaudern
        "chat_start": "Chat gestartet. Schreiben Sie 'exit' zum Beenden.",
        "chat_thinking": "Fred denkt nach...",
        "chat_error_api": "API-Fehler: {error}",
        "chat_empty_input": "Bitte geben Sie eine Nachricht ein.",
        "chat_clear_history": "Chat-Verlauf gelöscht.",
        
        # Coder / Programmierer
        "coder_mode": "Coder Modus aktiviert.",
        "coder_generating": "Generiere Code...",
        "coder_save_prompt": "Code speichern unter?",
        
        # Files & System / Dateien & System
        "file_not_found": "Datei nicht gefunden: {path}",
        "file_saved": "Datei gespeichert: {path}",
        "dir_list": "Inhaltsverzeichnis:",
        "sys_executing": "Führe Befehl aus...",
        "sys_permission_denied": "Zugriff verweigert.",
        
        # Settings / Einstellungen
        "settings_title": "--- EINSTELLUNGEN ---",
        "settings_language": "Sprache ändern (de/en)",
        "settings_api_key": "API Schlüssel setzen",
        "settings_model": "Modell auswählen",
        "settings_saved": "Einstellungen gespeichert.",
        
        # Errors / Fehlermeldungen
        "err_network": "Netzwerkfehler. Bitte Verbindung prüfen.",
        "err_timeout": "Zeitüberschreitung der Anfrage.",
        "err_invalid_json": "Ungültiges JSON Format.",
        "err_missing_key": "API Schlüssel fehlt in den Einstellungen.",
    },
    "en": {
        # General / Allgemein
        "welcome": "Welcome to Fred!",
        "goodbye": "Goodbye!",
        "exit_prompt": "Exit (exit/quit)?",
        "invalid_choice": "Invalid choice. Please try again.",
        "loading": "Loading...",
        "error": "Error",
        "success": "Success",
        "confirm": "Confirm",
        "cancel": "Cancel",
        
        # Menu / Menü
        "main_menu": "--- MAIN MENU ---",
        "menu_chat": "1. Start Chat",
        "menu_coder": "2. Coder Mode",
        "menu_notes": "3. Manage Notes",
        "menu_projects": "4. Manage Projects",
        "menu_files": "5. Browse Files",
        "menu_settings": "6. Settings",
        "menu_exit": "0. Exit",
        "select_option": "Select an option",
        
        # Chat / Plaudern
        "chat_start": "Chat started. Type 'exit' to quit.",
        "chat_thinking": "Fred is thinking...",
        "chat_error_api": "API Error: {error}",
        "chat_empty_input": "Please enter a message.",
        "chat_clear_history": "Chat history cleared.",
        
        # Coder / Programmierer
        "coder_mode": "Coder mode activated.",
        "coder_generating": "Generating code...",
        "coder_save_prompt": "Save code to?",
        
        # Files & System / Dateien & System
        "file_not_found": "File not found: {path}",
        "file_saved": "File saved: {path}",
        "dir_list": "Directory listing:",
        "sys_executing": "Executing command...",
        "sys_permission_denied": "Permission denied.",
        
        # Settings / Einstellungen
        "settings_title": "--- SETTINGS ---",
        "settings_language": "Change language (de/en)",
        "settings_api_key": "Set API Key",
        "settings_model": "Select Model",
        "settings_saved": "Settings saved.",
        
        # Errors / Fehlermeldungen
        "err_network": "Network error. Please check connection.",
        "err_timeout": "Request timed out.",
        "err_invalid_json": "Invalid JSON format.",
        "err_missing_key": "API Key missing in settings.",
    }
}

class LanguageManager:
    def __init__(self):
        self.current_lang = "de"  # Default language

    def set_language(self, lang_code):
        if lang_code in TRANSLATIONS:
            self.current_lang = lang_code
            return True
        return False

    def get(self, key, **kwargs):
        """
        Get translation for key. Supports formatting with kwargs.
        Example: get('file_not_found', path='/tmp/test.txt')
        """
        text = TRANSLATIONS[self.current_lang].get(key, f"[Missing: {key}]")
        try:
            return text.format(**kwargs)
        except KeyError:
            return text

    def get_current_code(self):
        return self.current_lang

# Global instance / Globale Instanz
lang = LanguageManager()

def t(key, **kwargs):
    """Shortcut for translation / Kurzform für Übersetzung"""
    return lang.get(key, **kwargs)
