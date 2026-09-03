import logging
import sys


class SafeFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "t_id"):
            record.t_id = "-"
        return super().format(record)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = SafeFormatter(
        "%(levelname)s | %(name)s | %(filename)s:%(lineno)d | t_id=%(t_id)s | %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]


def get_logger(name, t_id: str = None):
    logger = logging.getLogger(name)
    if t_id:
        return logging.LoggerAdapter(logger, {"t_id": t_id})
    return logger
