import logging.config
from pathlib import Path
from pythonjsonlogger import jsonlogger

# Define project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configure logging
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": jsonlogger.JsonFormatter,
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "json_default": str,
            "json_ensure_ascii": False
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": str(PROJECT_ROOT / "app.log"),
            "maxBytes": 1024 * 1024,  # 1MB
            "backupCount": 5
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Apply logging configuration
logging.config.dictConfig(log_config)

# Create logger
logger = logging.getLogger(__name__)

# Example of how to use structured logging:
# logger.info("User action", extra={
#     "user_id": "123",
#     "action": "login",
#     "ip_address": "192.168.1.1"
# }) 