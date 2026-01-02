import logging
from logging.handlers import TimedRotatingFileHandler
import os

# ---- Paths ----
PROJECT_DIR = ""
LOG_DIR = "logs"
LOG_FILE = "app.log"

log_dir_path = os.path.join(PROJECT_DIR, LOG_DIR)
log_file_path = os.path.join(log_dir_path, LOG_FILE)

# ---- Ensure log directory exists ----
os.makedirs(log_dir_path, exist_ok=True)

# ---- Logging handler ----
handler = TimedRotatingFileHandler(
    filename=log_file_path, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
handler.setFormatter(formatter)

# ---- Logger setup (NOT root) ----
logger = logging.getLogger("project_1")
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(handler)

