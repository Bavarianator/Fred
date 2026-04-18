# ~/fred/forge_ui.py
"""FRED GUI - Frontend für die Terminal-Module"""

import sys
import os
import threading
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTabWidget, QLabel, QComboBox, QInputDialog, QMessageBox,
    QSplitter, QFrame, QToolBar
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QAction

# FRED Module importieren
from fred_db import init_db, connect as db_connect
from fred_chat import chat
from fred_notes import create_note as add_note, get_notes, delete_note, get_note as get_note_by_id, update_note, get_categories as get_note_categories
from fred_projects import (
    create_project as add_project, get_projects, delete_project, get_project as get_project_by_id,
    get_tasks, create_task as add_task, update_task as toggle_task, delete_task
)
from fred_settings import get_setting, save_setting


# Signal-Brücke für Thread-sichere UI Updates
class SignalBridge(QObject):
    chat_response = Signal(str)
    chat_error = Signal(str)

bridge = SignalBridge()


# ═══════════════════════════════════════
# CHAT TAB
# ═══════════════════════════════════════
class ChatTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Chat-Verlauf
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 11))
        self.chat_display.setStyleSheet("background-color: #1a1a2e; color: #e0e0e0; padding: 10px;")
        layout.addWidget(self.chat_display)

        # Eingabe
        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Nachricht an FRED...")
        self.input_field.setFont(QFont("Consolas", 11))
        self.input_field.setStyleSheet("background-color: #16213e; color: #fff; padding: 8px; border-radius: 5px;")
        self.input_field.returnPressed.connect(self.send_message)
        input_row.addWidget(self.input_field)

        self.send_btn = QPushButton("Senden")
        self.send_btn.setStyleSheet("background-color: #0f3460; color: #fff; padding: 8px 16px; border-radius: 5px;")
        self.send_btn.clicked.connect(self.send_message)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

        # Signals
        bridge.chat_response.connect(self.show_response)
        bridge.chat_error.connect(self.show_error)

        self.chat_display.append("🤖 FRED: Hallo! Wie kann ich helfen?\n")

    def send_message(self):
        msg = self.input_field.text().strip()
        if not msg:
            return
        self.input_field.clear()
        self.chat_display.append(f"👤 Du: {msg}\n")
        self.send_btn.setEnabled(False)

        # Chat in Thread (blockiert nicht UI)
        def run():
            try:
                response = chat(msg)
                bridge.chat_response.emit(response)
            except Exception as e:
                bridge.chat_error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def show_response(self, text):
        self.chat_display.append(f"🤖 FRED: {text}\n")
        self.send_btn.setEnabled(True)

    def show_error(self, text):
        self.chat_display.append(f"❌ Fehler: {text}\n")
        self.send_btn.setEnabled(True)


# ═══════════════════════════════════════
# NOTIZEN TAB
# ═══════════════════════════════════════
class NotesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)

        # Links: Liste
        left = QVBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Suchen...")
        self.search.setStyleSheet("padding: 6px; background: #16213e; color: #fff; border-radius: 4px;")
        self.search.textChanged.connect(self.load_notes)
        left.addWidget(self.search)

        self.note_list = QListWidget()
        self.note_list.setStyleSheet("background: #1a1a2e; color: #e0e0e0; padding: 5px;")
        self.note_list.currentRowChanged.connect(self.show_note)
        left.addWidget(self.note_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ Neu")
        add_btn.clicked.connect(self.new_note)
        del_btn = QPushButton("🗑️ Löschen")
        del_btn.clicked.connect(self.del_note)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        for btn in [add_btn, del_btn]:
            btn.setStyleSheet("background: #0f3460; color: #fff; padding: 6px; border-radius: 4px;")
        left.addLayout(btn_row)

        # Rechts: Editor
        right = QVBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Titel")
        self.title_edit.setStyleSheet("padding: 6px; background: #16213e; color: #fff; font-size: 14px; border-radius: 4px;")
        right.addWidget(self.title_edit)

        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel("Kategorie:"))
        self.cat_edit = QLineEdit()
        self.cat_edit.setPlaceholderText("Allgemein")
        self.cat_edit.setStyleSheet("padding: 4px; background: #16213e; color: #fff; border-radius: 4px;")
        cat_row.addWidget(self.cat_edit)
        right.addLayout(cat_row)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Inhalt...")
        self.content_edit.setStyleSheet("background: #1a1a2e; color: #e0e0e0; padding: 8px;")
        self.content_edit.setFont(QFont("Consolas", 11))
        right.addWidget(self.content_edit)

        save_btn = QPushButton("💾 Speichern")
        save_btn.setStyleSheet("background: #0f3460; color: #fff; padding: 8px; border-radius: 4px;")
        save_btn.clicked.connect(self.save_note)
        right.addWidget(save_btn)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setMaximumWidth(300)
        right_widget = QWidget()
        right_widget.setLayout(right)

        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        self.notes_data = []
        self.load_notes()

    def load_notes(self):
        search = self.search.text().strip() or None
        self.notes_data = get_notes(search=search)
        self.note_list.clear()
        for n in self.notes_data:
            self.note_list.addItem(f"[{n[0]}] {n[1]} ({n[3]})")

    def show_note(self, row):
        if row < 0 or row >= len(self.notes_data):
            return
        n = self.notes_data[row]
        self.title_edit.setText(n[1] or "")
        self.content_edit.setText(n[2] or "")
        self.cat_edit.setText(n[3] or "")

    def new_note(self):
        title, ok = QInputDialog.getText(self, "Neue Notiz", "Titel:")
        if ok and title:
            nid = add_note(title, "", "Allgemein", "")
            self.load_notes()

    def save_note(self):
        row = self.note_list.currentRow()
        if row < 0 or row >= len(self.notes_data):
            QMessageBox.warning(self, "Fehler", "Keine Notiz ausgewählt.")
            return
        nid = self.notes_data[row][0]
        update_note(nid,
                    title=self.title_edit.text(),
                    content=self.content_edit.toPlainText(),
                    category=self.cat_edit.text())
        self.load_notes()

    def del_note(self):
        row = self.note_list.currentRow()
        if row < 0 or row >= len(self.notes_data):
            return
        nid = self.notes_data[row][0]
        reply = QMessageBox.question(self, "Löschen", f"Notiz #{nid} löschen?")
        if reply == QMessageBox.Yes:
            delete_note(nid)
            self.load_notes()
            self.title_edit.clear()
            self.content_edit.clear()
            self.cat_edit.clear()


# ═══════════════════════════════════════
# PROJEKTE TAB
# ═══════════════════════════════════════
class ProjectsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)

        # Links: Projekte
        left = QVBoxLayout()
        left.addWidget(QLabel("📁 Projekte"))
        self.proj_list = QListWidget()
        self.proj_list.setStyleSheet("background: #1a1a2e; color: #e0e0e0;")
        self.proj_list.currentRowChanged.connect(self.show_project)
        left.addWidget(self.proj_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ Neu")
        add_btn.clicked.connect(self.new_project)
        del_btn = QPushButton("🗑️ Löschen")
        del_btn.clicked.connect(self.del_project)
        for btn in [add_btn, del_btn]:
            btn.setStyleSheet("background: #0f3460; color: #fff; padding: 6px; border-radius: 4px;")
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        left.addLayout(btn_row)

        # Rechts: Tasks
        right = QVBoxLayout()
        self.proj_label = QLabel("Projekt wählen...")
        self.proj_label.setFont(QFont("Arial", 13, QFont.Bold))
        self.proj_label.setStyleSheet("color: #e94560;")
        right.addWidget(self.proj_label)

        self.task_list = QListWidget()
        self.task_list.setStyleSheet("background: #1a1a2e; color: #e0e0e0;")
        self.task_list.itemDoubleClicked.connect(self.toggle_task_done)
        right.addWidget(self.task_list)

        task_btns = QHBoxLayout()
        add_task_btn = QPushButton("➕ Task")
        add_task_btn.clicked.connect(self.new_task)
        del_task_btn = QPushButton("🗑️ Task löschen")
        del_task_btn.clicked.connect(self.del_task)
        for btn in [add_task_btn, del_task_btn]:
            btn.setStyleSheet("background: #0f3460; color: #fff; padding: 6px; border-radius: 4px;")
        task_btns.addWidget(add_task_btn)
        task_btns.addWidget(del_task_btn)
        right.addLayout(task_btns)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setMaximumWidth(300)
        right_widget = QWidget()
        right_widget.setLayout(right)

        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        self.projects_data = []
        self.tasks_data = []
        self.load_projects()

    def load_projects(self):
        self.projects_data = get_projects()
        self.proj_list.clear()
        for p in self.projects_data:
            self.proj_list.addItem(f"[{p[0]}] {p[1]} ({p[3]})")

    def show_project(self, row):
        if row < 0 or row >= len(self.projects_data):
            return
        p = self.projects_data[row]
        self.proj_label.setText(f"📁 {p[1]} - {p[3]}")
        self.load_tasks(p[0])

    def load_tasks(self, project_id):
        self.tasks_data = get_tasks(project_id)
        self.task_list.clear()
        for t in self.tasks_data:
            icon = "✅" if t[3] else "⬜"
            self.task_list.addItem(f"{icon} [{t[0]}] {t[2]}")

    def new_project(self):
        name, ok = QInputDialog.getText(self, "Neues Projekt", "Name:")
        if ok and name:
            add_project(name)
            self.load_projects()

    def del_project(self):
        row = self.proj_list.currentRow()
        if row < 0:
            return
        pid = self.projects_data[row][0]
        reply = QMessageBox.question(self, "Löschen", f"Projekt #{pid} löschen?")
        if reply == QMessageBox.Yes:
            delete_project(pid)
            self.load_projects()

    def new_task(self):
        row = self.proj_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Erst Projekt wählen.")
            return
        pid = self.projects_data[row][0]
        title, ok = QInputDialog.getText(self, "Neuer Task", "Task:")
        if ok and title:
            add_task(pid, title)
            self.load_tasks(pid)

    def toggle_task_done(self, item):
        row = self.task_list.currentRow()
        if row < 0:
            return
        tid = self.tasks_data[row][0]
        toggle_task(tid)
        pid = self.projects_data[self.proj_list.currentRow()][0]
        self.load_tasks(pid)

    def del_task(self):
        row = self.task_list.currentRow()
        if row < 0:
            return
        tid = self.tasks_data[row][0]
        delete_task(tid)
        pid = self.projects_data[self.proj_list.currentRow()][0]
        self.load_tasks(pid)


# ═══════════════════════════════════════
# TOOLS TAB
# ═══════════════════════════════════════
class ToolsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("🛠️ System Tools"))

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        self.output.setStyleSheet("background: #0a0a0a; color: #00ff00; padding: 8px;")
        layout.addWidget(self.output)

        cmd_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Befehl eingeben...")
        self.cmd_input.setStyleSheet("padding: 6px; background: #16213e; color: #fff; border-radius: 4px;")
        self.cmd_input.returnPressed.connect(self.run_cmd)
        cmd_row.addWidget(self.cmd_input)

        run_btn = QPushButton("▶️ Ausführen")
        run_btn.setStyleSheet("background: #0f3460; color: #fff; padding: 6px; border-radius: 4px;")
        run_btn.clicked.connect(self.run_cmd)
        cmd_row.addWidget(run_btn)
        layout.addLayout(cmd_row)

        # Quick-Buttons
        quick = QHBoxLayout()
        for label, cmd in [("📊 Disk", "df -h"), ("🧠 RAM", "free -h"), ("⏱️ Uptime", "uptime"), ("🌐 IP", "hostname -I")]:
            btn = QPushButton(label)
            btn.setStyleSheet("background: #1a1a2e; color: #e0e0e0; padding: 6px; border-radius: 4px;")
            btn.clicked.connect(lambda checked, c=cmd: self.run_quick(c))
            quick.addWidget(btn)
        layout.addLayout(quick)

    def run_cmd(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        self.cmd_input.clear()
        self.execute(cmd)

    def run_quick(self, cmd):
        self.execute(cmd)

    def execute(self, cmd):
        import subprocess
        self.output.append(f"$ {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.stdout:
                self.output.append(result.stdout)
            if result.stderr:
                self.output.append(f"⚠️ {result.stderr}")
        except Exception as e:
            self.output.append(f"❌ {e}")
        self.output.append("")


# ═══════════════════════════════════════
# SETTINGS TAB
# ═══════════════════════════════════════
class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("⚙️ Einstellungen"))

        # API Key
        layout.addWidget(QLabel("OpenAI API Key:"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setStyleSheet("padding: 6px; background: #16213e; color: #fff; border-radius: 4px;")
        self.api_key.setText(get_setting("api_key") or "")
        layout.addWidget(self.api_key)

        # Model
        layout.addWidget(QLabel("Modell:"))
        self.model = QComboBox()
        self.model.addItems(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"])
        current = get_setting("model") or "gpt-4"
        idx = self.model.findText(current)
        if idx >= 0:
            self.model.setCurrentIndex(idx)
        self.model.setStyleSheet("padding: 6px; background: #16213e; color: #fff;")
        layout.addWidget(self.model)

        # System Prompt
        layout.addWidget(QLabel("System Prompt:"))
        self.system_prompt = QTextEdit()
        self.system_prompt.setStyleSheet("background: #1a1a2e; color: #e0e0e0; padding: 8px;")
        self.system_prompt.setText(get_setting("system_prompt") or "Du bist FRED, ein hilfreicher KI-Assistent.")
        layout.addWidget(self.system_prompt)

        save_btn = QPushButton("💾 Speichern")
        save_btn.setStyleSheet("background: #e94560; color: #fff; padding: 10px; font-size: 14px; border-radius: 5px;")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

        layout.addStretch()

    def save(self):
        save_setting("api_key", self.api_key.text().strip())
        save_setting("model", self.model.currentText())
        save_setting("system_prompt", self.system_prompt.toPlainText().strip())
        QMessageBox.information(self, "Gespeichert", "✅ Einstellungen gespeichert!")


# ═══════════════════════════════════════
# HAUPTFENSTER
# ═══════════════════════════════════════
class FredWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 FRED - Forge Resonance Engine Dashboard")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QMainWindow { background-color: #0a0a1a; }
            QTabWidget::pane { border: 1px solid #0f3460; background: #0a0a1a; }
            QTabBar::tab { background: #16213e; color: #e0e0e0; padding: 10px 20px; margin: 2px; border-radius: 4px; }
            QTabBar::tab:selected { background: #e94560; color: #fff; }
            QLabel { color: #e0e0e0; }
        """)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(ChatTab(), "💬 Chat")
        tabs.addTab(NotesTab(), "📝 Notizen")
        tabs.addTab(ProjectsTab(), "📁 Projekte")
        tabs.addTab(ToolsTab(), "🛠️ Tools")
        tabs.addTab(SettingsTab(), "⚙️ Settings")

        self.setCentralWidget(tabs)

        # Statusbar
        self.statusBar().showMessage(f"FRED bereit | Modell: {get_setting('model') or 'gpt-4'}")
        self.statusBar().setStyleSheet("color: #e0e0e0; background: #16213e;")


# ═══════════════════════════════════════
# START
# ═══════════════════════════════════════
def main():
    init_db()
    app = QApplication(sys.argv)
    window = FredWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
