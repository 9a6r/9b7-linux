"""Bilingual institutional Studio. The legacy analytics workspace stays available."""
from __future__ import annotations
import csv
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from .business import BusinessStore, BusinessError, CURRENCIES, database_path
from .windowing import show_workspace

AR = {
    "Welcome to Studio": "مرحبًا بك في Studio", "Create your organization": "إنشاء مؤسستك",
    "No business data has been created yet.": "لم تُنشأ أي بيانات أعمال بعد.",
    "Organization": "المؤسسة", "Industry": "نوع النشاط", "Currency": "العملة", "Language": "اللغة",
    "Save": "حفظ", "Cancel": "إلغاء", "Dashboard": "لوحة المعلومات", "Customers": "العملاء",
    "Products and stock": "المنتجات والمخزون", "Invoices": "الفواتير", "Audit": "سجل التدقيق",
    "Settings": "الإعدادات", "Name": "الاسم", "Phone": "الهاتف", "Email": "البريد الإلكتروني",
    "Notes": "ملاحظات", "SKU": "رمز المنتج", "Price": "السعر", "Stock": "المخزون",
    "Add": "إضافة", "Edit selected": "تعديل المحدد", "Search": "بحث", "Export CSV": "تصدير CSV",
    "New invoice": "فاتورة جديدة", "Customer": "العميل", "Product": "المنتج", "Quantity": "الكمية",
    "Add line": "إضافة بند", "Post invoice": "اعتماد الفاتورة", "Total": "الإجمالي", "Date": "التاريخ",
    "Invoice": "فاتورة", "Action": "العملية", "Entity": "نوع السجل", "Details": "التفاصيل",
    "Backup": "نسخ احتياطي", "Restore": "استعادة نسخة", "Flow and analytics": "Flow والتحليلات",
    "Open isolated demo": "فتح تجربة منفصلة", "Demo workspace": "مساحة تجريبية",
    "Sales": "المبيعات", "Units in stock": "الوحدات في المخزون", "Refresh": "تحديث",
    "Saved successfully": "تم الحفظ بنجاح", "Select a row first": "حدد سجلًا أولًا",
    "Confirm": "تأكيد", "Error": "خطأ", "ID": "الرقم",
    "Posting reduces stock and preserves this invoice permanently. Continue?": "اعتماد الفاتورة يخصم المخزون ويحفظها نهائيًا. هل تريد المتابعة؟",
    "Restore replaces current records; a backup of the current database is kept. Continue?": "الاستعادة تستبدل السجلات الحالية مع حفظ نسخة احتياطية منها. هل تريد المتابعة؟",
    "No sales yet": "لا توجد مبيعات بعد", "Sales by product": "المبيعات حسب المنتج",
    "required_field": "أكمل الحقول المطلوبة (حتى 500 حرف).", "invalid_money": "أدخل مبلغًا موجبًا أو صفرًا بمنزلتين عشريتين كحد أقصى.",
    "invalid_quantity": "أدخل كمية صحيحة موجبة.", "duplicate_sku": "رمز المنتج مستخدم بالفعل.",
    "insufficient_stock": "المخزون غير كافٍ أو المنتج غير موجود.", "customer_required": "اختر عميلًا موجودًا.",
    "empty_invoice": "أضف بندًا واحدًا على الأقل.", "organization_required": "أنشئ المؤسسة أولًا.",
    "currency_locked": "لا يمكن تغيير العملة بعد إصدار فواتير؛ فهذا يغيّر معنى المبالغ السابقة.",
    "invalid_settings": "إعدادات اللغة أو العملة غير صالحة.", "file_exists": "الملف موجود بالفعل. اختر اسمًا جديدًا.",
    "incompatible_database": "ملف غير صالح أو قاعدة بيانات بإصدار غير متوافق.",
    "Operation failed": "تعذر تنفيذ العملية. تحقق من الملف والصلاحيات وحاول مرة أخرى.",
    "System and services": "النظام والخدمات", "Choose organization data": "بيانات المؤسسة",
}
ERRORS = {
    "required_field": "Complete the required fields (up to 500 characters).",
    "invalid_money": "Enter a nonnegative amount with at most two decimal places.",
    "invalid_quantity": "Enter a positive whole quantity.", "duplicate_sku": "This SKU already exists.",
    "insufficient_stock": "Insufficient stock or missing product.", "customer_required": "Choose an existing customer.",
    "empty_invoice": "Add at least one invoice line.", "organization_required": "Create an organization first.",
    "currency_locked": "Currency cannot change after invoices have been posted.",
    "invalid_settings": "Invalid currency or language.", "file_exists": "File already exists; choose a new name.",
    "incompatible_database": "Invalid database or unsupported schema version.",
}


class BusinessStudio(QMainWindow):
    def __init__(self, store=None, demo=False):
        super().__init__()
        self.store = store or BusinessStore()
        self.demo = demo
        self.children_windows = []
        self.language = (self.store.organization() or {}).get("language", "ar")
        self.resize(1120, 760)
        self.render()

    def tr(self, text):
        return AR.get(text, text) if self.language == "ar" else ERRORS.get(text, text)

    def button(self, text, action):
        button = QPushButton(self.tr(text))
        button.clicked.connect(action)
        return button

    def guard(self, action):
        try:
            return action()
        except Exception as exc:
            key = str(exc) if isinstance(exc, BusinessError) else "Operation failed"
            QMessageBox.warning(self, self.tr("Error"), self.tr(key))
            return None

    def confirm(self, message):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(self.tr("Confirm"))
        dialog.setText(self.tr(message))
        yes = dialog.addButton(self.tr("Confirm"), QMessageBox.ButtonRole.AcceptRole)
        cancel = dialog.addButton(self.tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(cancel)
        dialog.exec()
        return dialog.clickedButton() == yes

    def render(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if self.language == "ar" else Qt.LayoutDirection.LeftToRight)
        org = self.store.organization()
        self.setWindowTitle("Studio — " + (self.tr("Demo workspace") if self.demo else org["name"] if org else "9b7"))
        frame = QWidget()
        layout = QVBoxLayout(frame)
        self.setCentralWidget(frame)
        heading = QLabel("Studio / " + (org["name"] if org else self.tr("Welcome to Studio")))
        heading.setStyleSheet("font-size:26px; font-weight:600; padding:16px")
        layout.addWidget(heading)
        if not org:
            layout.addWidget(QLabel(self.tr("No business data has been created yet.")))
            layout.addWidget(self.organization_form())
            layout.addWidget(self.button("Open isolated demo", self.open_demo))
            layout.addStretch()
            return
        if self.demo:
            label = QLabel(self.tr("Demo workspace"))
            label.setStyleSheet("background:#f2cf80;color:#33290e;padding:10px")
            layout.addWidget(label)
        tools = QHBoxLayout()
        tools.addWidget(self.button("Flow and analytics", self.open_flow))
        tools.addWidget(self.button("System and services", self.open_control))
        tools.addWidget(self.button("Refresh", self.render))
        layout.addLayout(tools)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.tabs.addTab(self.dashboard(), self.tr("Dashboard"))
        self.tabs.addTab(self.records_page("customers"), self.tr("Customers"))
        self.tabs.addTab(self.records_page("products"), self.tr("Products and stock"))
        self.tabs.addTab(self.invoices_page(), self.tr("Invoices"))
        audit = self.store.audit()
        self.tabs.addTab(self.table_page(audit, [("created_at", "Date"), ("action", "Action"), ("entity", "Entity"), ("record_id", "ID"), ("details", "Details")]), self.tr("Audit"))
        settings = QWidget(); box = QVBoxLayout(settings)
        box.addWidget(self.organization_form())
        box.addWidget(self.button("Backup", self.backup))
        box.addWidget(self.button("Restore", self.restore))
        box.addWidget(self.button("Open isolated demo", self.open_demo)); box.addStretch()
        self.tabs.addTab(settings, self.tr("Settings"))

    def organization_form(self):
        page = QWidget(); form = QFormLayout(page)
        org = self.store.organization() or {}
        self.org_name = QLineEdit(org.get("name", "")); self.org_name.setObjectName("organization_name")
        self.industry = QLineEdit(org.get("industry", ""))
        self.currency = QComboBox(); self.currency.addItems(CURRENCIES); self.currency.setCurrentText(org.get("currency", "EGP"))
        self.lang = QComboBox(); self.lang.addItem("العربية", "ar"); self.lang.addItem("English", "en")
        self.lang.setCurrentIndex(0 if self.language == "ar" else 1)
        if not org:
            self.lang.currentIndexChanged.connect(self.welcome_language)
        for name, widget in (("Organization", self.org_name), ("Industry", self.industry), ("Currency", self.currency), ("Language", self.lang)):
            form.addRow(self.tr(name), widget)
        form.addRow(self.button("Save", self.save_organization))
        return page

    def welcome_language(self):
        name, industry, currency = self.org_name.text(), self.industry.text(), self.currency.currentText()
        self.language = self.lang.currentData()
        self.render()
        self.org_name.setText(name); self.industry.setText(industry); self.currency.setCurrentText(currency)

    def save_organization(self):
        def save():
            self.store.save_organization(self.org_name.text(), self.industry.text(), self.currency.currentText(), self.lang.currentData())
            self.language = self.lang.currentData()
            self.render()
        self.guard(save)

    def dashboard(self):
        page = QWidget(); box = QVBoxLayout(page)
        data = self.store.dashboard(); currency = self.store.organization()["currency"]
        for key, name in (("customers", "Customers"), ("products", "Products and stock"), ("invoices", "Invoices"), ("stock", "Units in stock")):
            label = QLabel(f'{self.tr(name)}: {data[key]:,}'); label.setStyleSheet("font-size:20px;padding:5px")
            box.addWidget(label)
        box.addWidget(QLabel(f'{self.tr("Sales")}: {data["sales_minor"]/100:,.2f} {currency}'))
        # Chart uses actual posted invoice amounts, not generated samples.
        totals = self.store.sales_by_product()
        if totals:
            from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis
            chart = QChart(); chart.setTitle(self.tr("Sales by product") + " / " + currency)
            series = QBarSeries(); values = QBarSet(self.tr("Sales"))
            values.append([r[1]/100 for r in totals]); series.append(values); chart.addSeries(series)
            chart.createDefaultAxes(); axis = QBarCategoryAxis(); axis.append([r[0] for r in totals])
            chart.setAxisX(axis, series); box.addWidget(QChartView(chart))
        else:
            box.addWidget(QLabel(self.tr("No sales yet"))); box.addStretch()
        return page

    def fill_table(self, table, rows, columns):
        table.setSortingEnabled(False); table.setRowCount(len(rows)); table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([self.tr(label) for _, label in columns])
        for row, record in enumerate(rows):
            for col, (key, _) in enumerate(columns):
                value = record[key]
                if key.endswith("_minor"):
                    value = f'{value/100:,.2f} {self.store.organization()["currency"]}'
                item = QTableWidgetItem(str(value)); item.setData(Qt.ItemDataRole.UserRole, record.get("id"))
                table.setItem(row, col, item)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True); table.resizeColumnsToContents(); table.horizontalHeader().setStretchLastSection(True)

    def table_page(self, rows, columns):
        page = QWidget(); box = QVBoxLayout(page); table = QTableWidget()
        self.fill_table(table, rows, columns); box.addWidget(table)
        box.addWidget(self.button("Export CSV", lambda: self.export(rows, columns)))
        return page

    def records_page(self, entity):
        page = QWidget(); box = QVBoxLayout(page); search = QLineEdit(); search.setPlaceholderText(self.tr("Search"))
        table = QTableWidget(); box.addWidget(search); box.addWidget(table)
        columns = [("name", "Name"), ("phone", "Phone"), ("email", "Email"), ("notes", "Notes")] if entity == "customers" else [("sku", "SKU"), ("name", "Name"), ("price_minor", "Price"), ("stock", "Stock")]
        def refresh(): self.fill_table(table, self.store.records(entity, search.text()), columns)
        search.textChanged.connect(refresh); refresh()
        def edit():
            row = table.currentRow()
            if row < 0:
                QMessageBox.information(self, "Studio", self.tr("Select a row first")); return
            record_id = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            record = next(r for r in self.store.records(entity) if r["id"] == record_id)
            self.edit_record(entity, record)
        tools = QHBoxLayout(); tools.addWidget(self.button("Add", lambda: self.edit_record(entity)))
        tools.addWidget(self.button("Edit selected", edit))
        tools.addWidget(self.button("Export CSV", lambda: self.export(self.store.records(entity, search.text()), columns)))
        box.addLayout(tools); return page

    def edit_record(self, entity, record=None):
        record = record or {}; dialog = QDialog(self); dialog.setWindowTitle(self.tr("Customers" if entity == "customers" else "Products and stock"))
        form = QFormLayout(dialog); fields = {}
        specs = [("name", "Name"), ("phone", "Phone"), ("email", "Email"), ("notes", "Notes")] if entity == "customers" else [("sku", "SKU"), ("name", "Name"), ("price", "Price"), ("stock", "Stock")]
        for key, label in specs:
            widget = QSpinBox() if key == "stock" else QLineEdit()
            if key == "stock": widget.setRange(0, 10**9); widget.setValue(record.get(key, 0))
            else: widget.setText(f'{record["price_minor"]/100:.2f}' if key == "price" and record else str(record.get(key, "")))
            fields[key] = widget; form.addRow(self.tr(label), widget)
        def save():
            def action():
                values = {key: widget.value() if key == "stock" else widget.text() for key, widget in fields.items()}
                method = self.store.save_customer if entity == "customers" else self.store.save_product
                method(**values, record_id=record.get("id")); dialog.accept(); self.render()
            self.guard(action)
        form.addRow(self.button("Save", save), self.button("Cancel", dialog.reject)); dialog.exec()

    def invoices_page(self):
        page = self.table_page(self.store.invoices(), [("id", "ID"), ("customer", "Customer"), ("created_at", "Date"), ("total_minor", "Total")])
        page.layout().insertWidget(0, self.button("New invoice", self.new_invoice)); return page

    def new_invoice(self):
        dialog = QDialog(self); dialog.setWindowTitle(self.tr("New invoice")); dialog.resize(650, 450)
        box = QVBoxLayout(dialog); customer = QComboBox()
        for row in self.store.records("customers"): customer.addItem(row["name"], row["id"])
        box.addWidget(QLabel(self.tr("Customer"))); box.addWidget(customer)
        product = QComboBox()
        for row in self.store.records("products"): product.addItem(f'{row["sku"]} · {row["name"]} ({row["stock"]})', row["id"])
        qty = QSpinBox(); qty.setRange(1, 10**9)
        form = QFormLayout(); form.addRow(self.tr("Product"), product); form.addRow(self.tr("Quantity"), qty); box.addLayout(form)
        table = QTableWidget(0, 2); table.setHorizontalHeaderLabels([self.tr("Product"), self.tr("Quantity")]); table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lines = []
        def add():
            if product.currentData() is None: return
            lines.append((product.currentData(), qty.value())); row = table.rowCount(); table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(product.currentText())); table.setItem(row, 1, QTableWidgetItem(str(qty.value())))
        box.addWidget(self.button("Add line", add)); box.addWidget(table)
        def post():
            if not self.confirm("Posting reduces stock and preserves this invoice permanently. Continue?"): return
            def action(): self.store.post_invoice(customer.currentData(), lines); dialog.accept(); self.render()
            self.guard(action)
        box.addWidget(self.button("Post invoice", post)); box.addWidget(self.button("Cancel", dialog.reject)); dialog.exec()

    def export(self, rows, columns):
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export CSV"), "studio.csv", "CSV (*.csv)")
        if not path: return
        def action():
            with open(path, "w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream); writer.writerow([key for key, _ in columns])
                for row in rows:
                    # Spreadsheet formula injection protection for user-entered cells.
                    writer.writerow([("'" + str(row[key])) if str(row[key]).startswith(("=", "+", "-", "@")) else row[key] for key, _ in columns])
        self.guard(action)

    def backup(self):
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Backup"), "studio-backup.sqlite3", "SQLite (*.sqlite3)")
        if path: self.guard(lambda: self.store.backup(path))

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Restore"), "", "SQLite (*.sqlite3)")
        if path and self.confirm("Restore replaces current records; a backup of the current database is kept. Continue?"):
            def action():
                self.store.restore(path); self.language = (self.store.organization() or {}).get("language", "ar"); self.render()
            self.guard(action)

    def open_flow(self):
        from .studio import Studio
        window = Studio(); show_workspace(window); self.children_windows.append(window)

    def open_control(self):
        from .control_center import ControlCenter
        window = ControlCenter(); window.show(); self.children_windows.append(window)

    def open_demo(self):
        def action():
            store = BusinessStore(database_path().parent / "demo/organization.sqlite3")
            if not store.organization():
                store.save_organization("Studio Demo", "Demo", "EGP", self.language)
                customer = store.save_customer("عميل تجريبي / Demo customer")
                product = store.save_product("DEMO-01", "منتج تجريبي / Demo product", "250.00", 20)
                store.post_invoice(customer, [(product, 2)])
            window = BusinessStudio(store, demo=True); show_workspace(window); self.children_windows.append(window)
        self.guard(action)

    def closeEvent(self, event):
        for window in self.children_windows:
            if getattr(window, "jobs", []):
                event.ignore(); return
            window.close()
        self.store.close(); event.accept()
