import io
import json
import logging
import os
import pprint
import sys
import traceback
from functools import wraps

# Dynamically determine addon name
try:
    # Get addon name from the module path
    module_path = os.path.dirname(__file__)
    ADDON_NAME = os.path.basename(module_path)
except Exception:
    logging.error(traceback.format_exc())
    raise Exception(
        "Failed to determine addon's name, is this logger in the addon root?"
    )

# Create a dedicated logs directory
log_dir = os.path.join(os.path.expanduser("~"), ".ayon/logs")
try:
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
except Exception:
    pass  # Continue even if directory creation fails

# Get a logger with a unique name
log = logging.getLogger(f"ayon.{ADDON_NAME}")

# Determine log level
log_level = os.getenv("AYON_LOG_LEVEL")
ayon_debug = os.getenv("AYON_DEBUG", False)
if ayon_debug:
    log.setLevel(logging.DEBUG)
else:
    if log_level:
        log.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    else:
        log.setLevel(logging.INFO)

# Clear existing handlers
for handler in log.handlers[:]:
    log.removeHandler(handler)

# Prevent interference from parent loggers
log.propagate = False


# Define a safe handler class that won't crash on None streams
class SafeStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        # Use a StringIO if stream is None
        self.fallback_stream = io.StringIO()
        super().__init__(stream or self.fallback_stream)

    def emit(self, record):
        try:
            # Check if stream is still valid
            if self.stream is None or not hasattr(self.stream, "write"):
                self.stream = self.fallback_stream
            super().emit(record)
            self.flush()
        except Exception:
            # Never fail on logging
            pass


# Add file handler only if AYON_DEBUG is enabled
if ayon_debug:
    try:
        file_path = os.path.join(log_dir, f"{ADDON_NAME}_debug.log")
        file_handler = logging.FileHandler(file_path)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        log.addHandler(file_handler)
    except Exception:
        print(f"Failed to create log file in {log_dir}")

# Add console handler with explicit stream and error handling
try:
    stream_handler = SafeStreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(
        logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    )
    stream_handler.setLevel(logging.DEBUG if ayon_debug else log.level)
    log.addHandler(stream_handler)
except Exception:
    print("Failed to create console log handler")


# Create safe logging methods that won't crash
def safe_log(func):
    @wraps(func)
    def wrapper(msg, *args, **kwargs):
        try:
            return func(msg, *args, **kwargs)
        except Exception:
            # Last resort - print directly to console
            print(f"SAFE LOG: {msg}")

    return wrapper


# Apply safe wrappers to all logging methods
log.debug = safe_log(log.debug)
log.info = safe_log(log.info)
log.warning = safe_log(log.warning)
log.error = safe_log(log.error)
log.critical = safe_log(log.critical)

# Print confirmation that logger is initialized
print(f"AYON {ADDON_NAME} logger initialized successfully")


# ===========================================================
# Define safe handler class that won't crash on None streams
# ===========================================================


class SafeStreamHandler(logging.StreamHandler):
    """
    A logging handler that safely handles None streams by using a StringIO fallback.
    """

    def __init__(self, stream=None):
        """
        Initialize the handler with a stream or a StringIO fallback.
        Args:
            stream (io.TextIOBase, optional): The stream to write logs to.
                If None, a StringIO fallback will be used.
        """
        # If stream is None, use a StringIO as a fallback
        # Use a StringIO if stream is None
        self.fallback_stream = io.StringIO()
        super().__init__(stream or self.fallback_stream)

    def emit(self, record):
        """
        Emit a record to the stream, ensuring the stream is valid.
        Args:
            record (logging.LogRecord): The log record to emit.
        """
        try:
            # Check if stream is still valid
            if self.stream is None or not hasattr(self.stream, "write"):
                self.stream = self.fallback_stream
            super().emit(record)
            self.flush()
        except Exception:
            # Never fail on logging
            pass


# ===========================================================
# Log formatting functions
# ===========================================================


# format log function to handle large data structures in debug logs
def format_log(data, max_length=5000):
    """
    Format data for logging, truncating if necessary.
    Args:
        data (any): The data to format.
        max_length (int): Maximum length of the formatted string.
    Returns:
        str: Formatted string representation of the data.
    """
    if not isinstance(data, (dict, list)):
        return str(data)

    try:
        # Try JSON formatting first (for JS/JSON data)

        formatted = json.dumps(data, indent=2, sort_keys=True)
    except (TypeError, ValueError):
        # Fall back to pprint for Python objects that aren't JSON serializable

        formatted = pprint.pformat(data, indent=2, width=100)

    if len(formatted) > max_length:
        return formatted[:max_length] + f"... (truncated, {len(formatted)} bytes total)"
    return formatted
