"""Run with QT_QPA_PLATFORM=offscreen in an environment with Qt system libraries."""
from pathlib import Path
import json
import os
import tempfile
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from nineb7.studio import Studio, STYLE

with tempfile.TemporaryDirectory() as state:
    os.environ["XDG_STATE_HOME"] = state
    app = QApplication([])
    app.setStyleSheet(STYLE)
    window = Studio()
    window.show()
    window.run_demo()
    loop = QEventLoop()
    timer = QTimer()
    timer.setInterval(50)
    timer.timeout.connect(lambda: loop.quit() if not window.jobs else None)
    timer.start()
    QTimer.singleShot(15000, loop.quit)
    loop.exec()
    assert not window.jobs, "GUI import failed to finish"
    assert window.report and window.report["kpis"]["orders"] == 8
    window.run_query()
    loop.exec()
    assert not window.jobs, "GUI query failed to finish"
    assert window.table.rowCount() == 4
    screenshot = Path(os.environ.get("NINEB7_SCREENSHOT", "/tmp/9b7-studio.png"))
    assert window.grab().save(str(screenshot))
    window.close()
    print("GUI smoke passed: real import, KPIs, database query, and screenshot")
