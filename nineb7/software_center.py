"""A small software catalog using Arch's signed repositories and the AI Hub."""
from pathlib import Path
import shutil
import subprocess
import sys
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)

# Reviewed choices; the root helper validates the same allowlist independently.
CATALOG = {
    "firefox": ("Firefox", False), "thunar": ("Thunar", False),
    "dbeaver": ("DBeaver", False), "btop": ("btop", False),
    "nodejs": ("Node.js — Gemini CLI runtime", False),
    "ollama": ("Ollama — optional local AI runtime (CPU)", True),
    "libreoffice-fresh": ("LibreOffice — optional office suite", True),
    "gimp": ("GIMP — optional image editor", True),
}


def package_version(key):
    if key not in CATALOG: raise ValueError("Unknown package")
    if not shutil.which("pacman"): return None
    result = subprocess.run(["pacman", "-Q", key], capture_output=True, text=True, timeout=10)
    return result.stdout.strip() if result.returncode == 0 else None


def system_action(action, key):
    if key not in CATALOG or action not in ("install", "remove", "start", "stop"):
        raise ValueError("Unsupported package action")
    if action == "remove" and not CATALOG[key][1]:
        raise ValueError("Core applications cannot be removed from this catalog")
    if action in ("start", "stop") and key != "ollama":
        raise ValueError("Unsupported runtime")
    helper = Path("/usr/local/bin/9b7-system-package")
    if not helper.is_file(): raise RuntimeError("This action requires the 9b7 live or installed system")
    return subprocess.Popen(["xfce4-terminal", "--hold", "--execute", "sudo", str(helper), action, key], start_new_session=True)


class SoftwareCenter(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("9b7 Software Center · مركز البرامج"); self.resize(960, 700)
        frame = QWidget(); box = QVBoxLayout(frame); self.setCentralWidget(frame)
        label = QLabel("Install on demand from signed Arch repositories.\nالتثبيت عند الطلب من مستودعات Arch الموقعة.\n"
                       "Installation opens a terminal for your administrator password and pacman's final package/size confirmation.\n"
                       "Arch requires a full system upgrade with new packages; review its download and disk sizes before accepting.\n"
                       "Live-session changes disappear after reboot unless installed on disk.")
        label.setWordWrap(True); box.addWidget(label)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); box.addWidget(scroll)
        items = QWidget(); grid = QGridLayout(items); scroll.setWidget(items); self.states = {}
        for row, (key, (name, removable)) in enumerate(CATALOG.items()):
            grid.addWidget(QLabel(name), row, 0); state = QLabel(); self.states[key] = state; grid.addWidget(state, row, 1)
            install = QPushButton("Install / update · تثبيت / تحديث")
            install.clicked.connect(lambda checked=False, k=key: self.action("install", k)); grid.addWidget(install, row, 2)
            if removable:
                remove = QPushButton("Remove · إزالة"); remove.clicked.connect(lambda checked=False, k=key: self.action("remove", k)); grid.addWidget(remove, row, 3)
        for action, label in (("start", "Start Ollama · تشغيل"), ("stop", "Stop Ollama · إيقاف")):
            button = QPushButton(label); button.clicked.connect(lambda checked=False, a=action: self.action(a, "ollama")); box.addWidget(button)
        info = QLabel("Ollama listens locally and downloads no model automatically. Start only one Ollama runtime; stop the Docker Local AI service before using the native runtime.")
        info.setWordWrap(True); box.addWidget(info)
        hub = QPushButton("AI Hub — Claude, Codex, OpenCode, Gemini, Copilot and local models")
        hub.clicked.connect(lambda: subprocess.Popen([sys.executable, "-m", "nineb7.ai_hub"], start_new_session=True)); box.addWidget(hub)
        refresh = QPushButton("Refresh installed status · تحديث الحالة"); refresh.clicked.connect(self.refresh); box.addWidget(refresh); self.refresh()

    def refresh(self):
        for key, label in self.states.items(): label.setText(package_version(key) or "Not installed · غير مثبت")

    def action(self, operation, key):
        text = f"{operation}: {CATALOG[key][0]}\nThe terminal shows the final operation before package changes.\nستظهر تفاصيل العملية في الطرفية قبل تغيير الحزم."
        if QMessageBox.question(self, "Software Center", text, defaultButton=QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        try: system_action(operation, key)
        except Exception as exc: QMessageBox.warning(self, "Software Center", str(exc))


def main():
    app = QApplication(sys.argv); app.setDesktopFileName("9b7-software-center")
    window = SoftwareCenter(); window.show(); return app.exec()


if __name__ == "__main__": raise SystemExit(main())
