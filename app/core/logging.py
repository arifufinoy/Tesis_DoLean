import logging.config


def configure_logging(level: str = "INFO") -> None:
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
        "handlers": {"default": {"class": "logging.StreamHandler", "formatter": "default", "stream": "ext://sys.stdout"}},
        "root": {"level": level, "handlers": ["default"]},
    })

