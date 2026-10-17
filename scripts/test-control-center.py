#!/usr/bin/env python3
"""Functional Qt smoke: async UI delivery, real Flow and SQLite query."""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QThread, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402
from nineb7.control_center import ControlCenter  # noqa: E402

with tempfile.TemporaryDirectory(prefix="9b7-gui-test-") as state:
    os.environ["XDG_STATE_HOME"] = state
    os.environ["XDG_CACHE_HOME"] = state
    app = QApplication([])
    window = ControlCenter()
    window.show()
    phase = [0]
    errors = []
    window.show_error = lambda error: (errors.append(error), app.exit(1))

    def step():
        try:
            if window.jobs:
                return
            assert QThread.currentThread() == app.thread()
            if phase[0] == 0:
                assert "memory_mb" in window.snapshot.toPlainText()
                # This closure crashed before TaskResult acquired GUI affinity.
                def callback(value):
                    assert QThread.currentThread() == app.thread()
                    window.snapshot.setPlainText(value)
                window.task(lambda: "GUI thread delivery", callback)
                phase[0] = 1
            elif phase[0] == 1:
                assert window.snapshot.toPlainText() == "GUI thread delivery"
                window.run_demo()
                phase[0] = 2
            elif phase[0] == 2:
                assert window.report["kpis"]["revenue"] == 39100
                window.query.setPlainText("SELECT COUNT(*) FROM orders")
                window.run_query()
                phase[0] = 3
            else:
                assert window.table.item(0, 0).text() == "8"
                print("PASS: Qt main-thread callback, system status, Flow demo and real SQLite query")
                app.quit()
        except Exception as exc:
            errors.append(repr(exc))
            app.exit(1)

    timer = QTimer()
    timer.timeout.connect(step)
    timer.start(100)
    QTimer.singleShot(20000, lambda: app.exit(2))
    result = app.exec()
    if result:
        print("GUI smoke failed:", errors or "timeout", file=sys.stderr)
    # Do not destroy QThreads while an operation is still running on failure.
    for thread, _ in list(window.jobs):
        thread.quit()
        thread.wait(6000)
    raise SystemExit(result)
