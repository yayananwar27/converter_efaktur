import multiprocessing
import os
from dotenv import load_dotenv
load_dotenv()
from logging.handlers import RotatingFileHandler

bind = "{0}:{1}".format(os.environ['HOST'], os.environ['PORT'])
#bind = "unix:/opt/jakwifi/jakflowapi.sock"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 43200
# File log Gunicorn
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = "log/gunicorn.log"

# Gunicorn logconfig
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "default",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["file", "console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["file", "console"],
            "propagate": False,
        },
    },
}

errorlog = log_file
accesslog = log_file