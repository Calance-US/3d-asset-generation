import logging.config
from pathlib import Path
from pythonjsonlogger import jsonlogger

# Get the project root directory (backend folder)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Custom JSON formatter
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = self.formatTime(record)
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        if hasattr(record, 'extra'):
            log_record.update(record.extra)

# Log configuration
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": CustomJsonFormatter,
            "format": "%(timestamp)s %(level)s %(module)s %(function)s %(line)s %(message)s"
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
            "maxBytes": 1048576,  # 1MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Configure logging
logging.config.dictConfig(log_config)

# Define logger
logger = logging.getLogger(__name__)

# Example of how to use structured logging:
# logger.info("User action", extra={
#     "user_id": "123",
#     "action": "login",
#     "ip_address": "192.168.1.1"
# }) 