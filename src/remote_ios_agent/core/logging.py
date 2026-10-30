import json
import logging
import os
import sys

from remote_ios_agent.core.models import timestamp

logger = logging.getLogger("remote_ios_agent.events")
logger.addHandler(logging.NullHandler())


def configure_logging():
    level = os.getenv("REMOTE_IOS_LOG_LEVEL", "WARNING").upper()
    logger.setLevel(getattr(logging, level, logging.WARNING))
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.propagate = False


def event(operation: str, session_id: str, status: str):
    # Intentionally exclude arguments, input text, credentials and exception bodies.
    logger.info(
        json.dumps(
            {"timestamp": timestamp(), "operation": operation, "session_id": session_id, "status": status}
        )
    )
