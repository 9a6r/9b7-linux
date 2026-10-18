"""User-run installer UI; the root backend receives settings through a pipe."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QInputDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)
from .installer import InstallConfig, SESSIONS, disks

LABELS = {
    'en': ['Install 9b7', 'Language', 'Target disk', 'Refresh disks', 'New username', 'New password', 'Repeat password',
           'Computer name', 'Timezone', 'Keyboard', 'Desktop session', 'Review installation',
           'Whole-disk installation only. ALL files on the selected disk will be erased. Dual boot is not supported.\n'
           'The Live account 9b7/9b7 is for testing only. Create your own permanent account.'],
    'ar': ['تثبيت 9b7', 'اللغة', 'القرص المستهدف', 'تحديث الأقراص', 'اسم مستخدم جديد', 'كلمة مرور جديدة', 'تكرار كلمة المرور',
           'اسم الجهاز', 'المنطقة الزمنية', 'لوحة المفاتيح', 'جلسة سطح المكتب', 'مراجعة التثبيت',
           'التثبيت يستخدم قرصًا كاملًا ويمسح جميع ملفاته. الإقلاع المزدوج غير مدعوم.\n'
           'حساب 9b7/9b7 للتجربة الحية فقط؛ أنشئ حسابك الدائم وكلمة مرور جديدة.'],
}


class Installer(QMainWindow):
    def __init__(self):
        super().__init__(); self.resize(850, 780); self.process = None; self.pending = None
        self.stdout_buffer = ''; self.stderr_buffer = ''; self.auth_attempts = 0
        frame = QWidget(); box = QVBoxLayout(frame); self.setCentralWidget(frame)
        self.notice = QLabel(); self.notice.setWordWrap(True); box.addWidget(self.notice)
        self.form_widget = QWidget(); form = QFormLayout(self.form_widget); box.addWidget(self.form_widget)
        self.language = QComboBox(); self.language.addItem('العربية', 'ar_EG.UTF-8'); self.language.addItem('English', 'en_US.UTF-8')
        self.disk = QComboBox(); self.refresh = QPushButton(); self.refresh.clicked.connect(self.refresh_disks)
        self.username = QLineEdit(); self.password = QLineEdit(); self.repeat = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password); self.repeat.setEchoMode(QLineEdit.EchoMode.Password)
        self.hostname = QLineEdit('9b7-pc'); self.timezone = QComboBox(); self.timezone.setEditable(True)
        self.timezone.addItems(['Africa/Cairo', 'UTC', 'Asia/Riyadh', 'Europe/London', 'America/New_York'])
        self.keyboard = QComboBox(); self.keyboard.addItems(['us,ara', 'us', 'ara'])
        self.session = QComboBox()
        for key, label in [('desk','DEsk'), ('desk-2d','DEsk 2D Fallback'), ('hyprland','Hyprland'), ('xfce','XFCE')]: self.session.addItem(label, key)
        self.labels = []
        for widget in (self.language, self.disk, self.refresh, self.username, self.password, self.repeat, self.hostname, self.timezone, self.keyboard, self.session):
            label = QLabel(); self.labels.append(label); form.addRow(label, widget)
        self.begin = QPushButton(); self.begin.clicked.connect(self.review); box.addWidget(self.begin)
        self.output = QPlainTextEdit(); self.output.setReadOnly(True); self.output.setMaximumBlockCount(1000); box.addWidget(self.output)
        self.status = QLabel(); self.status.setWordWrap(True); box.addWidget(self.status)
        self.language.currentIndexChanged.connect(self.translate); self.translate(); self.refresh_disks()

    def translate(self):
        self.arabic = self.language.currentData() == 'ar_EG.UTF-8'; text = LABELS['ar' if self.arabic else 'en']
        self.setWindowTitle(text[0]); self.notice.setText(text[12]); self.begin.setText(text[11])
        self.refresh.setText(text[3])
        for label, value in zip(self.labels, text[1:11]): label.setText(value)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if self.arabic else Qt.LayoutDirection.LeftToRight)

    def refresh_disks(self):
        self.disk.clear(); self.disk.addItem('اختر القرص / Select disk', None)
        try:
            for item in disks():
                unavailable = item['ro'] or item['mounted']
                title = f'{item["name"]} · {int(item["size"])/1024**3:.1f} GiB · {item.get("model") or ""}'
                if unavailable: title += ' [mounted/read-only · غير متاح]'
                self.disk.addItem(title, item['name'])
                if unavailable: self.disk.model().item(self.disk.count()-1).setEnabled(False)
        except Exception as exc: self.status.setText(str(exc))

    def configuration(self):
        if not self.disk.currentData(): raise ValueError('Select a disk · اختر قرصًا')
        if self.password.text() != self.repeat.text(): raise ValueError('Passwords do not match · كلمتا المرور غير متطابقتين')
        return InstallConfig(disk=self.disk.currentData(), username=self.username.text().strip(), password=self.password.text(),
            hostname=self.hostname.text().strip(), timezone=self.timezone.currentText(), language=self.language.currentData(),
            keyboard=self.keyboard.currentText(), session=self.session.currentData()).validate(require_confirmation=False)

    def review(self):
        try: config = self.configuration()
        except Exception as exc: QMessageBox.warning(self, '9b7', str(exc)); return
        summary = (f'{self.disk.currentText()}\nUser / المستخدم: {config.username}\n{config.hostname} · {config.timezone}\n'
                   f'{config.language} · {config.keyboard} · {self.session.currentText()}\n\n'
                   f'ALL DATA ON {config.disk} WILL BE ERASED.\nسيتم مسح جميع بيانات هذا القرص.\n'
                   f'Type / اكتب: ERASE {config.disk}')
        answer, accepted = QInputDialog.getText(self, 'Final confirmation · التأكيد النهائي', summary)
        if not accepted: return
        config.confirmation = answer
        try: config.validate()
        except Exception as exc: QMessageBox.warning(self, '9b7', str(exc)); return
        self.start_install(config)

    def start_install(self, config):
        config.validate()
        if not Path('/run/archiso/bootmnt').is_dir():
            QMessageBox.warning(self, '9b7', 'Run this installer in the Live ISO · شغّل المثبت من النظام الحي'); return
        self.pending = config; self.form_widget.setEnabled(False); self.begin.setEnabled(False)
        self.output.clear(); self.stdout_buffer = ''; self.stderr_buffer = ''; self.auth_attempts = 0
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        # No password appears in arguments, environment, a temporary file or logs.
        self.process.start('sudo', ['-k', '-S', '-p', '9B7_AUTHENTICATION:', '/usr/local/bin/9b7-install', '--config-stdin'])
        self.status.setText('Administrator authentication · التحقق من صلاحية الإدارة')

    def read_output(self):
        self.stdout_buffer += bytes(self.process.readAllStandardOutput()).decode(errors='replace')
        marker = '9B7_READY_FOR_CONFIGURATION'
        if marker in self.stdout_buffer and self.pending is not None:
            self.process.write((json.dumps(asdict(self.pending), ensure_ascii=False) + '\n').encode())
            self.process.closeWriteChannel(); self.pending = None
            self.password.clear(); self.repeat.clear()
            self.stdout_buffer = self.stdout_buffer.replace(marker, '')
            self.status.setText('Installing; do not power off · جارٍ التثبيت؛ لا تفصل الكهرباء')
        if self.pending is None or '\n' in self.stdout_buffer:
            self.output.appendPlainText(self.stdout_buffer); self.stdout_buffer = ''

    def read_error(self):
        self.stderr_buffer += bytes(self.process.readAllStandardError()).decode(errors='replace')
        marker = '9B7_AUTHENTICATION:'
        if marker in self.stderr_buffer:
            self.stderr_buffer = self.stderr_buffer.replace(marker, '')
            self.auth_attempts += 1
            password, accepted = QInputDialog.getText(self, 'Administrator · الإدارة',
                'Current Live password (9b7) · كلمة مرور الجلسة الحية الحالية (9b7)', QLineEdit.EchoMode.Password)
            if not accepted:
                self.process.closeWriteChannel(); self.process.terminate(); return
            self.process.write((password + '\n').encode())
        if '\n' in self.stderr_buffer:
            self.output.appendPlainText(self.stderr_buffer); self.stderr_buffer = ''

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.status.setText('Could not start administrator authentication · تعذر بدء التحقق')
            self.form_widget.setEnabled(True); self.begin.setEnabled(True); self.pending = None

    def finished(self, code, status):
        self.pending = None; self.password.clear(); self.repeat.clear()
        if code == 0 and status == QProcess.ExitStatus.NormalExit and 'INSTALLATION_COMPLETE:' in self.output.toPlainText():
            self.status.setText('Installation complete. Shut down and remove USB/ISO, then boot the disk.\nاكتمل التثبيت؛ أغلق الجهاز وأزل الفلاشة/ISO ثم أقلع من القرص.')
        else:
            self.status.setText('Installation did not complete. Read the log before retrying.\nلم يكتمل التثبيت؛ راجع السجل قبل إعادة المحاولة.')
            self.form_widget.setEnabled(True); self.begin.setEnabled(True)

    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.warning(self, '9b7', 'Installation is active. Wait for it to finish · انتظر انتهاء التثبيت')
            event.ignore()
        else: event.accept()


def main():
    app = QApplication(sys.argv); app.setDesktopFileName('9b7-install')
    window = Installer(); window.show(); return app.exec()


if __name__ == '__main__': raise SystemExit(main())
