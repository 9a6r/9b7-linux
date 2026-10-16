"""Single-user graduation lab; SQLite metadata is intentionally local."""
import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"
WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = False  # HTTP is bound to loopback on the host.
ENABLE_PROXY_FIX = False
FEATURE_FLAGS = {"ENABLE_TEMPLATE_PROCESSING": False}
SQLLAB_TIMEOUT = 60
