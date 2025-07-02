import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'ai_team.log')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

# Create a custom logger
logger = logging.getLogger('ai_team')
logger.setLevel(LOG_LEVEL)

# Formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')

# File handler with rotation
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)

# Add handlers if not already present (avoid duplicate logs)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Usage: from crewai_app.utils.logger import logger 