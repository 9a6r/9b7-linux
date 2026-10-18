"""Agent catalog and local-model management without reading authentication files."""
from __future__ import annotations
import json
import sys

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QGridLayout,
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget)
from . import software
from .studio import Studio

from .ai_runtime import MODELS, hardware, ollama_request, model_action, read_codex_usage


class Progress(QObject):
    changed = Signal(object, object)


class AIHub(Studio):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("AI Hub · مركز الذكاء الاصطناعي")
        self.resize(1060, 760)
        self.jobs = []
        self.progress_signal = Progress(self); self.progress_signal.changed.connect(self.progress_changed)
        frame = QWidget(); box = QVBoxLayout(frame)
        title = QLabel("AI Hub / 9b7"); title.setStyleSheet("font-size:28px;padding:12px;font-weight:bold")
        box.addWidget(title)
        label = QLabel("Install only what you choose · ثبّت ما تختاره فقط\nCloud agents use their official login and billing. Studio data is never sent automatically.")
        label.setWordWrap(True); box.addWidget(label)
        tabs = QTabWidget(); box.addWidget(tabs)
        tabs.addTab(self.agents_page(), "Agents · الوكلاء")
        tabs.addTab(self.models_page(), "Local models · النماذج المحلية")
        tabs.addTab(self.usage_page(), "Usage · الاستخدام")
        self.progress = QProgressBar(); box.addWidget(self.progress)
        self.status = QLabel("Ready · جاهز"); box.addWidget(self.status)
        self.setCentralWidget(frame)

    @Slot(object, object)
    def progress_changed(self, done, total):
        self.progress.setRange(0, 100 if total else 0)
        if total: self.progress.setValue(min(100, int(done * 100 / total)))

    def action_button(self, label, callback):
        button = QPushButton(label); button.clicked.connect(callback); return button

    def run_task(self, fn, message):
        if self.jobs:
            self.show_error("Wait for the active operation · انتظر انتهاء العملية الحالية"); return
        def completed(result):
            self.progress.setRange(0, 100); self.progress.setValue(100)
            self.status.setText(str(result or "Complete · اكتمل")); self.refresh_status()
        self.task(fn, completed, message)

    def show_error(self, text):
        self.progress.setRange(0, 100); self.progress.setValue(0)
        super().show_error(text)

    def closeEvent(self, event):
        child = getattr(self, "services_window", None)
        if child and child.jobs:
            self.show_error("Wait for the service operation · انتظر انتهاء عملية الخدمة")
            event.ignore(); return
        super().closeEvent(event)
        if event.isAccepted() and child: child.close()

    def agents_page(self):
        page = QWidget(); grid = QGridLayout(page); self.agent_labels = {}
        for row, (key, item) in enumerate(software.catalog().items()):
            label = QLabel(f'{item["title"]}\n{item["license"]} · {item["version"]}')
            label.setToolTip(item["auth"]); grid.addWidget(label, row, 0)
            state = QLabel(); self.agent_labels[key] = state; grid.addWidget(state, row, 1)
            grid.addWidget(self.action_button("Install / update · تثبيت / تحديث", lambda checked=False, k=key: self.install_agent(k)), row, 2)
            grid.addWidget(self.action_button("Launch · تشغيل", lambda checked=False, k=key: self.launch_agent(k)), row, 3)
            grid.addWidget(self.action_button("Remove · إزالة", lambda checked=False, k=key: self.remove_agent(k)), row, 4)
        row = len(self.agent_labels)
        grid.addWidget(QLabel("Updates use the reviewed version in this system's catalog.\nالتحديثات تستخدم الإصدار الذي تمت مراجعته في فهرس النظام."), row, 0, 1, 5)
        self.default = QComboBox(); self.default.addItems(software.catalog())
        prefs = software.data_root() / "preferences.json"
        if prefs.exists():
            try: self.default.setCurrentText(json.loads(prefs.read_text()).get("default", "claude"))
            except (OSError, ValueError): pass
        grid.addWidget(QLabel("Default agent · الوكيل الافتراضي"), row + 1, 0); grid.addWidget(self.default, row + 1, 1)
        grid.addWidget(self.action_button("Save · حفظ", self.save_default), row + 1, 2)
        self.refresh_status(); grid.setRowStretch(row + 2, 1); return page

    def refresh_status(self):
        for key, label in self.agent_labels.items():
            state = software.installed(key)
            label.setText(("Installed · مثبت\n" + state["version"]) if state else "Not installed · غير مثبت")

    def save_default(self):
        root = software.data_root(); root.mkdir(parents=True, exist_ok=True)
        (root / "preferences.json").write_text(json.dumps({"default": self.default.currentText()}) + "\n")
        self.status.setText("Default saved · تم حفظ الاختيار")

    def install_agent(self, key):
        item = software.entry(key)
        message = (f'{item["title"]} {item["version"]}\nDownload: {item["size"]/1024**2:.1f} MiB\n'
                   f'{item["auth"]}\nLicense: {item["license_url"]}\n\nDownload and install this tool only? · تنزيل وتثبيت هذه الأداة فقط؟')
        if QMessageBox.question(self, "Install · تثبيت", message, defaultButton=QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        self.run_task(lambda: (software.install(key, self.progress_signal.changed.emit), software.version(key))[1], "Downloading and verifying · تنزيل وتحقق…")

    def launch_agent(self, key):
        folder = QFileDialog.getExistingDirectory(self, "Choose the project to open · اختر مجلد المشروع")
        if folder:
            try: software.launch(key, folder)
            except Exception as exc: self.show_error(str(exc))

    def remove_agent(self, key):
        if QMessageBox.question(self, "Remove · إزالة", "Remove managed binaries? Login files and projects are preserved.\nإزالة ملفات البرنامج مع الاحتفاظ بالحساب والمشاريع؟", defaultButton=QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.run_task(lambda: software.remove(key), "Removing · إزالة…")

    def models_page(self):
        page = QWidget(); box = QVBoxLayout(page); info = hardware()
        label = QLabel(f'RAM {info["ram_mb"]} MiB · available {info["available_mb"]} MiB · CPU threads {info["cpu_threads"]}\n'
                       f'VRAM: {info["vram_mb"] if info["vram_mb"] is not None else "unknown / غير متاح"}\n'
                       f'Recommendation / اقتراح: {info["recommended"]}\n'
                       'Ollama is a local runtime. Start Local AI in Control Center; no model downloads automatically.\n'
                       'Ollama محلي. شغّل خدمة Local AI من مركز التحكم؛ لا يتم تنزيل نموذج تلقائيًا.')
        label.setWordWrap(True); box.addWidget(label)
        box.addWidget(self.action_button("Open local AI service · إدارة الخدمة المحلية", self.open_services))
        box.addWidget(self.action_button("Install native Ollama · تثبيت Ollama الأصلي", self.open_software))
        self.model = QComboBox(); self.model.addItems(MODELS); self.model.setCurrentText(info["recommended"]); box.addWidget(self.model)
        self.models_status = QTextEdit(); self.models_status.setReadOnly(True); box.addWidget(self.models_status)
        row = QHBoxLayout()
        for text, operation in (("Download · تنزيل", "pull"), ("Unload RAM · تفريغ الذاكرة", "unload"), ("Delete · حذف", "delete")):
            row.addWidget(self.action_button(text, lambda checked=False, op=operation: self.model_operation(op)))
        box.addLayout(row); box.addWidget(self.action_button("Refresh local models · تحديث القائمة", self.refresh_models)); return page

    def refresh_models(self):
        def read():
            with ollama_request("tags") as response: return json.load(response)
        if self.jobs: return
        self.task(read, lambda result: self.models_status.setPlainText(json.dumps(result, ensure_ascii=False, indent=2)), "Reading local models…")

    def model_operation(self, operation):
        name = self.model.currentText(); item = MODELS[name]
        if operation in ("pull", "delete"):
            text = f'{operation}: {name}\nApproximate download {item["download_mb"]} MB; working RAM about {item["working_mb"]} MB.\nContinue? · متابعة؟'
            if QMessageBox.question(self, "Local model · نموذج محلي", text, defaultButton=QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        self.run_task(lambda: model_action(name, operation, self.progress_signal.changed.emit), "Local model operation…")

    def open_software(self):
        import subprocess
        subprocess.Popen([sys.executable, "-m", "nineb7.software_center"], start_new_session=True)

    def open_services(self):
        from .control_center import ControlCenter
        if not hasattr(self, "services_window"): self.services_window = ControlCenter()
        self.services_window.tabs.setCurrentIndex(1); self.services_window.show()

    def usage_page(self):
        page = QWidget(); box = QVBoxLayout(page)
        text = QLabel("Claude usage: unavailable here. Use Claude's official /usage or account page.\nاستخدام Claude غير متاح هنا؛ استخدم /usage داخل البرنامج الرسمي.\n\nCodex: optionally choose a sessions folder to read local quota snapshots.\nThe timestamp is shown; old snapshots are not current live usage. No auth files are read.")
        text.setWordWrap(True); box.addWidget(text)
        self.usage = QTextEdit("No data selected · لم يتم اختيار بيانات"); self.usage.setReadOnly(True); box.addWidget(self.usage)
        box.addWidget(self.action_button("Choose Codex sessions · اختيار سجلات Codex", self.choose_usage)); return page

    def choose_usage(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Codex sessions folder · اختر مجلد الجلسات")
        if folder and not self.jobs:
            self.task(lambda: read_codex_usage(folder), self.display_usage, "Reading selected local snapshots…")

    def display_usage(self, rows):
        self.usage.setPlainText(json.dumps(rows, ensure_ascii=False, indent=2) if rows else "Usage unavailable · بيانات الاستخدام غير متاحة")
        self.status.setText("Local snapshot read · تمت قراءة اللقطة المحلية")


def main():
    app = QApplication(sys.argv); app.setApplicationName("AI Hub"); app.setDesktopFileName("9b7-ai-hub")
    window = AIHub(); window.show(); return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
