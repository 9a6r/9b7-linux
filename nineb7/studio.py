"""Native Qt desktop workspace for the 9b7 BIS graduation lab."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
from PySide6.QtCore import QObject, QThread, Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)
from . import __version__, agents, databases, flow, services

STYLE = """
QWidget { background:#101820; color:#e4f0ef; font-family:'Noto Sans'; font-size:14px; }
QLabel#brand { font-size:30px; font-weight:700; color:#70e5b6; }
QLabel#muted { color:#9bb3bc; }
QPushButton { background:#234238; padding:10px 18px; border:1px solid #3e6a59; border-radius:8px; }
QPushButton:hover { background:#32654f; } QPushButton:disabled { color:#71827f; background:#1e2a2c; }
QLineEdit,QTextEdit,QTableWidget,QComboBox { background:#182630; border:1px solid #304654; padding:8px; border-radius:6px; }
QHeaderView::section { background:#223641; padding:8px; }
QTabWidget::pane { border:1px solid #304654; padding:12px; }
QTabBar::tab { background:#182630; padding:12px 20px; } QTabBar::tab:selected { background:#295446; }
"""


class Worker(QObject):
    done = Signal(object)
    error = Signal(str)

    def __init__(self, function):
        super().__init__()
        self.function = function

    def run(self):
        try:
            self.done.emit(self.function())
        except Exception as exc:
            self.error.emit(str(exc))


class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("9b7 BIS Studio")
        self.resize(1120, 780)
        self.jobs = []
        self.report = None
        self.root = services.project_root()
        frame = QWidget()
        box = QVBoxLayout(frame)
        brand = QLabel("9b7 / BIS Studio")
        brand.setObjectName("brand")
        box.addWidget(brand)
        caption = QLabel("Business data → decisions → automation    |    مساحة عمل نظم معلومات الأعمال")
        caption.setObjectName("muted")
        box.addWidget(caption)
        tabs = QTabWidget()
        box.addWidget(tabs)
        tabs.addTab(self.data_page(), "Business pulse")
        tabs.addTab(self.services_page(), "Lab services")
        tabs.addTab(self.database_page(), "Database console")
        tabs.addTab(self.agents_page(), "AI team")
        tabs.addTab(self.help_page(), "Start here")
        self.status = QLabel("Ready · local-first · 8 GB profile · v" + __version__)
        self.status.setObjectName("muted")
        box.addWidget(self.status)
        self.setCentralWidget(frame)

    def task(self, function, complete, message="Working…"):
        self.status.setText(message)
        thread = QThread(self)
        worker = Worker(function)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(complete)
        worker.done.connect(thread.quit)
        worker.error.connect(self.show_error)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.jobs.remove((thread, worker)))
        thread.finished.connect(thread.deleteLater)
        self.jobs.append((thread, worker))
        thread.start()

    def show_error(self, text):
        self.status.setText("Action failed; see details")
        # Drivers may include DSNs in exception messages; redact current connection text.
        connection = self.connection.text() if hasattr(self, "connection") else ""
        if connection:
            text = text.replace(connection, "[connection redacted]")
        QMessageBox.warning(self, "9b7 Studio", text)

    def closeEvent(self, event):
        if self.jobs:
            QMessageBox.information(self, "Task running", "Wait for the active task before closing Studio.")
            event.ignore()
        else:
            event.accept()

    def data_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Import sales CSV, reject invalid rows, and calculate auditable KPIs. Re-imports do not duplicate orders."))
        row = QHBoxLayout()
        for title, fn in [("Run demo", self.run_demo), ("Import CSV…", self.choose_csv), ("Open report", self.open_report)]:
            button = QPushButton(title)
            button.clicked.connect(fn)
            row.addWidget(button)
        layout.addLayout(row)
        self.kpi = QLabel("No data yet. Run the bundled BIS demo to begin.")
        self.kpi.setStyleSheet("font-size:21px; padding:24px; color:#70e5b6")
        self.kpi.setWordWrap(True)
        layout.addWidget(self.kpi)
        self.results = QTableWidget(0, 3)
        self.results.setHorizontalHeaderLabels(["Product", "Units sold", "Revenue"])
        self.results.horizontalHeader().setStretchLastSection(True)
        self.results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.results)
        self.audit = QTextEdit()
        self.audit.setReadOnly(True)
        self.audit.setMaximumHeight(140)
        self.audit.setPlaceholderText("Import history and data-quality issues will appear here.")
        layout.addWidget(self.audit)
        return page

    def run_demo(self):
        self.import_csv(self.root / "data/demo-sales.csv")

    def choose_csv(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Sales CSV", "", "CSV (*.csv)")
        if filename:
            self.import_csv(Path(filename))

    def import_csv(self, filename):
        self.task(lambda: flow.run(filename, flow.state_dir() / "business.sqlite3", flow.state_dir() / "reports"),
                  self.imported, "Validating and importing sales…")

    def imported(self, result):
        self.report = result
        k = result["kpis"]
        self.kpi.setText(f'{k["orders"]} orders    /    Revenue {k["revenue"]:,.2f}    /    Profit {k["profit"]:,.2f}\n'
                         f'Margin {k["margin_percent"]}%   ·   Rejected rows: {result["rejected"]}')
        products = k["top_products"]
        self.results.setRowCount(len(products))
        for row, product in enumerate(products):
            for col, value in enumerate((product["product"], product["units"], f'{product["revenue"]:,.2f}')):
                self.results.setItem(row, col, QTableWidgetItem(str(value)))
        self.results.resizeColumnsToContents()
        lines = [f'Imported {result["inserted"]} new orders · {result["duplicates"]} duplicates skipped · {result["rejected"]} rows need review',
                 f'Audit reference: {result["run_id"]}']
        lines.extend(f'Row {error["line"]}: {error["reason"]}' for error in result["errors"][:20])
        self.audit.setPlainText("\n".join(lines))
        self.status.setText("Import complete · audit history saved in SQLite")

    def open_report(self):
        path = flow.state_dir() / "reports/report.html"
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            self.show_error("Import a CSV or run the demo first.")

    def services_page(self):
        page = QWidget()
        grid = QGridLayout(page)
        label = QLabel("8 GB laptop: run one heavy stack at a time. Data volumes survive Stop; a nonpersistent Live session does not survive reboot.")
        label.setWordWrap(True)
        grid.addWidget(label, 0, 0, 1, 4)
        for row, (key, item) in enumerate(services.CATALOG.items(), 1):
            grid.addWidget(QLabel(f'{item["title"]}\nEstimated RAM: {item["ram_mb"]} MB'), row, 0)
            for col, operation in enumerate(("start", "stop"), 1):
                button = QPushButton(operation.title())
                button.clicked.connect(lambda checked=False, k=key, op=operation: self.service(k, op))
                grid.addWidget(button, row, col)
            button = QPushButton("Open")
            button.setEnabled(bool(item["port"]))
            button.clicked.connect(lambda checked=False, port=item["port"]:
                                   QDesktopServices.openUrl(QUrl(f"http://127.0.0.1:{port}")))
            grid.addWidget(button, row, 3)
        grid.setRowStretch(len(services.CATALOG) + 1, 1)
        return page

    def service(self, key, op):
        if any(getattr(worker, "service_task", False) for _, worker in self.jobs):
            self.show_error("Wait for the current service operation to finish.")
            return
        self.task(lambda: services.action(key, op),
                  lambda _: self.status.setText(f"{services.CATALOG[key]['title']}: {op} complete"),
                  f"{op.title()} {key}… First initialization can take several minutes.")
        self.jobs[-1][1].service_task = True

    def database_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("One console · SQLite / PostgreSQL / MySQL / Cassandra / MongoDB / Redis · read-only · up to 200 rows"))
        self.engine = QComboBox()
        self.engine.addItems(databases.ENGINES)
        layout.addWidget(self.engine)
        self.connection = QLineEdit(str(flow.state_dir() / "business.sqlite3"))
        self.connection.setPlaceholderText("SQLite file path or database connection URI; kept only in memory")
        self.connection.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        layout.addWidget(self.connection)
        self.query = QTextEdit("SELECT product, SUM(quantity) AS units FROM orders GROUP BY product")
        self.query.setMaximumHeight(120)
        layout.addWidget(self.query)
        button = QPushButton("Run read-only query")
        button.clicked.connect(self.run_query)
        layout.addWidget(button)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        return page

    def run_query(self):
        engine, connection, statement = self.engine.currentText(), self.connection.text(), self.query.toPlainText()
        self.task(lambda: databases.query(engine, connection, statement), self.queried, "Querying database…")

    def queried(self, result):
        columns, rows = result
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
        self.status.setText(f"Query complete · showing {len(rows)} rows (limit {databases.LIMIT})")

    def agents_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("Analyst → Operations planner → Reviewer\nLocal Ollama model; only aggregate KPIs are shared. Suggestions require human judgment.")
        label.setWordWrap(True)
        layout.addWidget(label)
        button = QPushButton("Analyze current report")
        button.clicked.connect(self.analyze)
        layout.addWidget(button)
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        layout.addWidget(self.ai_output)
        return page

    def analyze(self):
        if not self.report:
            self.show_error("Run the demo or import a CSV first, then start Local AI from Lab services.")
            return
        self.task(lambda: agents.analyze(self.report),
                  self.analyzed,
                  "Three agents are reviewing the report; CPU inference can take several minutes…")

    def analyzed(self, notes):
        self.ai_output.setPlainText("\n\n".join(n["agent"].upper() + "\n" + n["text"] for n in notes))
        self.status.setText("Three-agent review complete · review suggestions before acting")

    def help_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText("""Welcome to 9b7 Linux / أهلاً بك

1. Start with Business pulse → Run demo. Your data stays local.
2. Try Database console against the generated SQLite database.
3. Start ONE lab stack. Open its web interface after startup completes.
4. For AI: start Local AI, then analyze the report. A full offline edition includes the model.

Linux username / password: 9b7 / 9b7
Super+Enter terminal · Super+D launcher · Super+B Firefox
Super+E file manager · Super+S Studio · Super+Q close · Super+L lock
Super+1…9 workspaces · Super+Shift+1…9 move window

Boot: choose Live, software-rendering compatibility, or existing OS.
VirtualBox: EFI optional, VMSVGA, 128 MB video RAM, 4 GB system RAM, 2 CPUs.
If Hyprland is unstable, choose XFCE in the login screen.
Live changes are temporary. Use an installed disk for persistent projects and Docker data.

App accounts: Superset 9b7/9b7; ERPNext Administrator/9b7.
n8n, Metabase and Odoo have their own first-run setup screens.
Full ISO bundles service images. Desktop ISO downloads them on first use.
See docs/USER-GUIDE.ar.md and docs/HANDOFF.md in /opt/9b7.
""")
        layout.addWidget(help_text)
        return page


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = Studio()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
