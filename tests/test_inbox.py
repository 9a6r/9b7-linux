import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from nineb7 import inbox


class InboxTests(unittest.TestCase):
    def test_files_are_processed_and_bad_input_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "9b7-Inbox"
            folder.mkdir()
            (folder / "good.csv").write_text("order_id,date,customer,product,quantity,unit_price,unit_cost\na,2026-10-16,Nile,Service,2,10,4\n")
            (folder / "bad.csv").write_text("wrong,columns\nx,y\n")
            with patch("nineb7.inbox.Path.home", return_value=root), patch.dict(os.environ, {"XDG_STATE_HOME": str(root / "state")}):
                inbox.main()
                inbox.main()
            self.assertEqual(len(list((folder / "processed").glob("*.csv"))), 1)
            self.assertEqual(len(list((folder / "failed").glob("*.csv"))), 1)
            self.assertFalse(list(folder.glob("*.csv")))
            with sqlite3.connect(root / "state/9b7/business.sqlite3") as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 1)
            self.assertEqual(len(list((root / "state/9b7/inbox-runs").glob("*/error.json"))), 1)


if __name__ == "__main__":
    unittest.main()
