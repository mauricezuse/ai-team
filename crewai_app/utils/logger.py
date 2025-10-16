import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'ai_team.log')
BACKEND_LOG_FILE = os.path.join(os.path.dirname(__file__), '../../backend.log')
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

# Backend file handler for uvicorn logs
backend_file_handler = RotatingFileHandler(BACKEND_LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
backend_file_handler.setLevel(LOG_LEVEL)
backend_file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)

# Add handlers if not already present (avoid duplicate logs)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(backend_file_handler)
    logger.addHandler(console_handler)

# Add handlers to all ai_team.* loggers
def attach_handlers_to_all_ai_team_loggers():
    for name in logging.root.manager.loggerDict:
        if name.startswith('ai_team.'):
            l = logging.getLogger(name)
            l.setLevel(LOG_LEVEL)
            l.propagate = True
            if not l.hasHandlers():
                l.addHandler(file_handler)
                l.addHandler(backend_file_handler)
                l.addHandler(console_handler)

attach_handlers_to_all_ai_team_loggers()

# Configure uvicorn logging to use our file handler
def configure_uvicorn_logging():
    """Configure uvicorn to log to our file handler"""
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.addHandler(backend_file_handler)
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.propagate = True
    
    # Also configure uvicorn.access for request logs
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.addHandler(backend_file_handler)
    access_logger.addHandler(console_handler)
    access_logger.propagate = True
    
    # Configure uvicorn.error for error logs
    error_logger = logging.getLogger("uvicorn.error")
    error_logger.addHandler(backend_file_handler)
    error_logger.addHandler(console_handler)
    error_logger.propagate = True

configure_uvicorn_logging()

# Test log lines for agent loggers
logging.getLogger('ai_team.developer').info('[LoggerTest] DeveloperAgent logger is active.')
logging.getLogger('ai_team.frontend').info('[LoggerTest] FrontendAgent logger is active.')

# Usage: from crewai_app.utils.logger import logger 