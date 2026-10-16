"""Idempotent initialization; errors are not suppressed."""
import os
import subprocess
from superset.app import create_app

subprocess.run(["superset", "db", "upgrade"], check=True)
app = create_app()
with app.app_context():
    manager = app.appbuilder.sm
    username = os.environ["LAB_ADMIN_USER"]
    if not manager.find_user(username=username):
        user = manager.add_user(username, "9b7", "BIS", "9b7@localhost.local", manager.find_role("Admin"),
                                os.environ["LAB_ADMIN_PASSWORD"])
        if not user:
            raise RuntimeError("Superset admin creation failed")
subprocess.run(["superset", "init"], check=True)
