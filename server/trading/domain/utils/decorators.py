from functools import wraps
import logging
import time
import asyncio

class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[33m",      # yellow
        logging.INFO: "\033[32m",       # green
        logging.WARNING: "\033[35m",    # magenta (optional)
        logging.ERROR: "\033[31m",      # red
        logging.CRITICAL: "\033[41m"    # red background
    }
    RESET = "\033[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{super().format(record)}{self.RESET}"

def logged(logger_name=None, level=logging.INFO):
    def decorator(func):

        lname = logger_name or func.__module__
        logger = logging.getLogger(lname)
        handler = logging.StreamHandler()
        fmt = "%(asctime)s %(name)s %(levelname)s: %(message)s"
        handler.setFormatter(ColoredFormatter(fmt))
        
        if not logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(level)

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                logger.log(level, f"CALL {func.__name__}")
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                except Exception:
                    logger.exception(f"EXCEPTION in {func.__name__}")
                    raise
                duration = time.perf_counter() - start
                logger.log(level, f"RETURN {func.__name__} → {result!r} in {duration:.4f}s")
                return result
            return wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger.log(level, f"CALL {func.__name__}")
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    logger.exception(f"EXCEPTION in {func.__name__}")
                    raise
                duration = time.perf_counter() - start
                logger.log(level, f"RETURN {func.__name__} → {result!r} in {duration:.4f}s")
                return result
            return wrapper
    return decorator