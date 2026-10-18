"""9b7 system and business-lab control center, sharing Studio's tested actions."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication, QGridLayout, QLabel, QMainWindow, QPushButton, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget,
)
from . import services
from .studio import Studio

# Commands are fixed argument lists, never shell fragments from the UI.
TOOLS = {
    "Desktop settings · سطح المكتب": ["desk-settings"],
    "Network · الشبكة": ["nm-connection-editor"],
    "Sound · الصوت": ["pavucontrol"],
    "Displays · الشاشات": ["wdisplays"],
    "Bluetooth · بلوتوث": ["blueman-manager"],
    "Appearance · المظهر": ["nwg-look"],
    "System monitor · الموارد": ["xfce4-terminal", "-e", "btop"],
    "BIS Studio": ["9b7-studio"],
    "AI Hub · مركز الذكاء الاصطناعي": ["9b7-ai-hub"],
    "Software Center · مركز البرامج": ["9b7-software-center"],
    "Database workbench · قواعد البيانات": ["dbeaver"],
    "Terminal · الطرفية": ["xfce4-terminal"],
}


def system_snapshot() -> dict:
    """Read local status without starting services or requesting privileges."""
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable"):
            memory[key] = round(int(value.split()[0]) / 1024)
    commands = {
        "NetworkManager": ["systemctl", "is-active", "NetworkManager"],
        "Docker": ["systemctl", "is-active", "docker"],
        "PipeWire": ["systemctl", "--user", "is-active", "pipewire"],
    }
    state = {"desktop": os.environ.get("XDG_CURRENT_DESKTOP", "unknown"),
             "session": os.environ.get("XDG_SESSION_TYPE", "unknown"),
             "memory_mb": memory}
    for label, command in commands.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
            state[label] = result.stdout.strip() or "unavailable"
        except (OSError, subprocess.TimeoutExpired):
            state[label] = "unavailable"
    return state


class ControlCenter(Studio):
    """Reuse service/database/AI pages; Studio remains a separate application."""
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("9b7 Control Center · مركز التحكم")
        self.setWindowIcon(QIcon.fromTheme("9b7-control-center"))
        self.resize(1060, 740)
        self.jobs = []
        self.report = None
        self.root = services.project_root()
        frame = QWidget()
        layout = QVBoxLayout(frame)
        title = QLabel("9b7 / Control Center · مركز التحكم")
        title.setStyleSheet("font-size:24px; font-weight:bold; padding:12px")
        layout.addWidget(title)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.tabs.addTab(self.system_page(), "System · النظام")
        self.tabs.addTab(self.services_page(), "Services · الخدمات")
        self.tabs.addTab(self.database_page(), "Databases · قواعد البيانات")
        self.tabs.addTab(self.agents_page(), "AI agents · الوكلاء")
        self.tabs.addTab(self.data_page(), "9b7 Flow · الأتمتة")
        self.tabs.addTab(self.about_page(), "About · عن النظام")
        self.status = QLabel("Ready · جاهز — الخدمات الثقيلة تعمل عند الطلب")
        layout.addWidget(self.status)
        self.setCentralWidget(frame)
        QTimer.singleShot(0, self.refresh)

    def system_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.snapshot = QTextEdit()
        self.snapshot.setReadOnly(True)
        self.snapshot.setMaximumHeight(170)
        layout.addWidget(self.snapshot)
        refresh = QPushButton("Refresh status · تحديث الحالة")
        refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)
        grid = QGridLayout()
        for i, (title, command) in enumerate(TOOLS.items()):
            button = QPushButton(title)
            button.setMinimumHeight(45)
            button.setEnabled(shutil.which(command[0]) is not None)
            button.clicked.connect(lambda checked=False, args=command: self.launch(args))
            grid.addWidget(button, i // 2, i % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def refresh(self):
        if getattr(self, "refreshing", False):
            return
        self.refreshing = True

        def completed(state):
            self.snapshot.setPlainText(json.dumps(state, ensure_ascii=False, indent=2))
            self.refreshing = False
            self.status.setText("Status updated · تم تحديث الحالة")

        self.task(system_snapshot, completed, "Reading system status…")

    def launch(self, args):
        try:
            subprocess.Popen(args, start_new_session=True)
        except OSError as exc:
            self.show_error(str(exc))

    def about_page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        text = QLabel(
            "9b7 — BIS graduation workspace\n\n"
            "Desktop: DEsk v0.1.2 BETA by the DEsk authors (MIT).\n"
            "Original room, icons and GTK theme preserved.\n"
            "Login: Slot-SDDM-6 by l4k1 (GPLv3).\n"
            "Boot: arch-slider-and-glow by Hasan Agit Ünal (MIT).\n\n"
            "Super+A: applications • Super+D: drawer • Super+L: lock\n"
            "Super+Enter: terminal • Super+C: DEsk settings\n"
            "Alt+Shift: العربية / English • Super+N: notifications\n\n"
            "DEsk's shell interface currently uses English. Arabic input is configured;\n"
            "upstream Cairo text drawing does not yet provide full Arabic shaping/RTL.\n"
            "Qt/GTK applications provide their own Arabic text support.\n\n"
            "8GB RAM: start one heavy service at a time. Desktop downloads service\n"
            "images on first use; Full bundles them. Live data needs persistent storage."
        )
        text.setWordWrap(True)
        box.addWidget(text)
        docs = QPushButton("Project documentation · دليل المشروع")
        docs.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://github.com/9a6r/9b7-linux")))
        box.addWidget(docs)
        box.addStretch()
        return page


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("9b7 Control Center")
    app.setDesktopFileName("9b7-control-center")
    window = ControlCenter()
    if "--flow" in sys.argv:
        window.tabs.setCurrentIndex(4)
    elif "--services" in sys.argv:
        window.tabs.setCurrentIndex(1)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
