import logging
from logging import config


def setup_logging(log_level: str):
    logging.getLogger("httpcore").setLevel(logging.INFO)

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s"
            },
            "simple": {"format": "%(levelname)s - %(name)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "level": log_level,
            },
        },
        "loggers": {
            "randouyin": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "test": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "httpx": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }
    config.dictConfig(LOGGING_CONFIG)
