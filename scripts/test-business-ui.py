#!/usr/bin/env python3
"""Exercise blank onboarding, saved language/layout, Arabic data and chart UI."""
import os
from pathlib import Path
import sys
import tempfile
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from nineb7.business import BusinessStore
from nineb7.business_ui import BusinessStudio

with tempfile.TemporaryDirectory(prefix="9b7-business-ui-") as temp:
    os.environ["XDG_STATE_HOME"] = temp
    os.environ["XDG_CACHE_HOME"] = temp
    app = QApplication([])
    path = Path(temp) / "institution.sqlite3"
    window = BusinessStudio(BusinessStore(path)); window.show(); app.processEvents()
    assert window.store.organization() is None
    assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft
    window.org_name.setText("شركة النور"); window.industry.setText("صيانة")
    window.save_organization(); app.processEvents()
    assert window.tabs.tabText(1) == "العملاء"
    customer = window.store.save_customer("أحمد علي")
    product = window.store.save_product("A-01", "قطعة غيار", "12.50", 5)
    window.store.post_invoice(customer, [(product, 2)])
    window.render(); app.processEvents()
    assert window.store.dashboard()["sales_minor"] == 2500
    output = Path(os.environ.get("NINEB7_BUSINESS_SCREENSHOT", "/tmp/9b7-business-ar.png"))
    assert window.grab().save(str(output))
    window.lang.setCurrentIndex(1); window.save_organization(); app.processEvents()
    assert window.tabs.tabText(1) == "Customers"
    assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
    window.close()
    reopened = BusinessStudio(BusinessStore(path)); reopened.show(); app.processEvents()
    assert reopened.language == "en"
    assert reopened.store.records("customers", "أحمد")[0]["name"] == "أحمد علي"
    assert reopened.store.dashboard()["invoices"] == 1
    reopened.close()
    print("PASS: empty first run, Arabic/RTL, real records/invoice/chart, English/LTR and persisted restart")
