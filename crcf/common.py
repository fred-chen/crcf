"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

import logging
import os
import sys
from threading import RLock

# custom log level for step messages, between INFO(20) and WARNING(30)
STEP = 25
logging.addLevelName(STEP, "STEP")

g_prog_name = os.path.basename(sys.argv[0])

logger = logging.getLogger("crcf")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter(
            "[%(levelname)s][%(asctime)s][%(progname)s : %(clsname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class _CtxFilter(logging.Filter):
    def filter(self, record):
        record.progname = g_prog_name
        return True


logger.addFilter(_CtxFilter())


class Common:
    """Common class provides some common functions to be used by other classes."""

    UNIQIDENTIFIER = "CRCF_NO_WAY_OF_DUPLICATION:"
    step_number = 0

    _LEVEL_MAP = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
    }

    def log(self, msg, level=3):
        """Log a message to stdout.

        Args:
            msg: the message to be logged.
            level: the level of the message.
                0: critical, 1: error, 2: warning, 3: info, 99: step. Default is 3.
        """
        clsname = self.__class__.__name__
        if level == 99:
            logger.log(
                STEP,
                f"\n\nSTEP {Common.step_number}: {msg}\n\n",
                extra={"clsname": clsname},
            )
        else:
            logger.log(
                self._LEVEL_MAP.get(level, logging.INFO),
                msg,
                extra={"clsname": clsname},
            )

    def warn(self, msg):
        """Log a warning message."""
        self.log(msg, 2)

    def info(self, msg):
        """Log an information message."""
        self.log(msg, 3)

    def error(self, msg):
        """Log an error message."""
        self.log(msg, 1)

    def critical(self, msg):
        """Log a critical message."""
        self.log(msg, 0)

    def step(self, msg):
        """Log a step message with the auto-increamental step number."""
        Common.step_number += 1
        self.log(msg, 99)


class LockAble:
    """A LockAble object."""

    def __init__(self):
        self.lck = RLock()

    def lock(self, blocking=1):
        """Acquire the lock."""
        self.lck.acquire(blocking)

    def unlock(self):
        """Release the lock."""
        self.lck.release()
