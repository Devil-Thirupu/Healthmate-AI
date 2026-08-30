import logging
import re
import sys

class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive tokens, passwords, and PII from log output."""
    SENSITIVE_PATTERNS = [
        (re.compile(r'(password[\'"]?\s*[:=]\s*[\'"]?)([^\'",\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(token[\'"]?\s*[:=]\s*[\'"]?)([^\'",\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(bearer\s+)([a-zA-Z0-9\-_.]+)', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(pin[\'"]?\s*[:=]\s*[\'"]?)([^\'",\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        return True

def setup_logger(name: str = "healthmate") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(stream_handler)
    return logger

logger = setup_logger()
