#!/usr/bin/env python3
"""Validate selection/identity/confirmation without any block-device writes."""
import os
from pathlib import Path
import sys
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog
from nineb7.installer_ui import Installer
app = QApplication([])
with patch('nineb7.installer_ui.disks', return_value=[{'name':'/dev/vda','size':80*1024**3,'model':'TEST DISPOSABLE ONLY','ro':False,'mounted':False}]):
    window = Installer(); window.show(); app.processEvents()
assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft
assert window.disk.currentData() is None
try: window.configuration(); raise AssertionError('No disk selected but accepted')
except ValueError: pass
window.disk.setCurrentIndex(1); window.username.setText('student')
window.password.setText('Test-only-password'); window.repeat.setText('Test-only-password')
assert window.configuration().session == 'desk'
with patch.object(QInputDialog, 'getText', return_value=('ERASE /dev/sda', True)), patch.object(QMessageBox,'warning'), patch.object(window,'start_install') as start:
    window.review(); start.assert_not_called()
with patch.object(QInputDialog, 'getText', return_value=('ERASE /dev/vda', True)), patch.object(window,'start_install') as start:
    window.review(); start.assert_called_once(); assert start.call_args.args[0].username == 'student'
window.language.setCurrentIndex(1); app.processEvents()
assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
window.password.clear(); window.repeat.clear()
assert window.grab().save(str(Path(os.environ.get('NINEB7_INSTALLER_SCREENSHOT','/tmp/9b7-installer.png'))))
window.close()
print('PASS: no automatic disk selection, identity validation, exact confirmation gate, Arabic/English layout. No disk writes performed.')
