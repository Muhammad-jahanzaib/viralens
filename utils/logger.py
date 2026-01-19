"""
Logging Utility for Royal Research Automation System

This module provides a comprehensive logging system with:
- Dual output: Console (INFO+) and File (DEBUG+)
- Daily log rotation with automatic cleanup
- Color-coded console output
- Detailed file logs with context information
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Try to import colorama for colored console output
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

# Get log directory from config, or use default
try:
    from config import LOGS_DIR
except ImportError:
    LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "logs")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)


# ============================================================================
# COLOR MAPPING (if colorama is available)
# ============================================================================

if COLORAMA_AVAILABLE:
    LOG_COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
else:
    LOG_COLORS = {}


# ============================================================================
# CUSTOM FORMATTER WITH COLORS
# ============================================================================

class ColoredConsoleFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors if available.

        Args:
            record: Log record to format

        Returns:
            Formatted log message with colors
        """
        if COLORAMA_AVAILABLE and record.levelname in LOG_COLORS:
            # Add color to level name
            record.levelname = f"{LOG_COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"

        return super().format(record)


# ============================================================================
# LOG CLEANUP FUNCTION
# ============================================================================

def cleanup_old_logs(days_to_keep: int = 30) -> int:
    """
    Delete log files older than specified number of days.

    Args:
        days_to_keep: Number of days to keep logs (default: 30)

    Returns:
        Number of log files deleted

    Example:
        >>> deleted = cleanup_old_logs(7)  # Keep only last 7 days
        >>> print(f"Deleted {deleted} old log files")
    """
    deleted_count = 0
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    try:
        log_dir = Path(LOGS_DIR)

        # Find all log files
        for log_file in log_dir.glob("research_*.log"):
            try:
                # Get file modification time
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)

                # Delete if older than cutoff
                if file_time < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1

            except Exception as e:
                # Skip files we can't process
                print(f"Warning: Could not process log file {log_file}: {e}", file=sys.stderr)
                continue

    except Exception as e:
        print(f"Warning: Error during log cleanup: {e}", file=sys.stderr)

    return deleted_count


# ============================================================================
# LOGGER SETUP FUNCTION
# ============================================================================

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create and configure a logger with console and file handlers.

    Args:
        name: Logger name (typically module name)
        level: Logging level (default: logging.INFO)

    Returns:
        Configured logger instance

    Features:
        - Console handler: INFO+ with simple format and colors
        - File handler: DEBUG+ with detailed format
        - Daily log rotation (new file per day)
        - Automatic cleanup of old logs (30 days)
        - UTF-8 encoding support
        - Prevents duplicate handlers

    Example:
        >>> logger = setup_logger("my_module", logging.DEBUG)
        >>> logger.info("System started")
        >>> logger.error("Something went wrong")
    """
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # ========================================================================
    # CONSOLE HANDLER (INFO+)
    # ========================================================================

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)  # Respect the requested level

    # Simple format for console: [HH:MM:SS] LEVEL - Message
    console_format = "[%(asctime)s] %(levelname)s - %(message)s"
    console_date_format = "%H:%M:%S"

    console_formatter = ColoredConsoleFormatter(
        console_format,
        datefmt=console_date_format
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # ========================================================================
    # FILE HANDLER (DEBUG+)
    # ========================================================================

    try:
        # Generate daily log filename: research_2024-01-15.log
        log_filename = f"research_{datetime.now().strftime('%Y-%m-%d')}.log"
        log_filepath = os.path.join(LOGS_DIR, log_filename)

        file_handler = logging.FileHandler(
            log_filepath,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Detailed format for file: YYYY-MM-DD HH:MM:SS - module - LEVEL - function:line - Message
        file_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )
        file_date_format = "%Y-%m-%d %H:%M:%S"

        file_formatter = logging.Formatter(
            file_format,
            datefmt=file_date_format
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Log the log file location (only once)
        logger.debug(f"Logging to file: {log_filepath}")

    except Exception as e:
        # Graceful degradation: Continue with console-only logging
        print(f"Warning: Could not create file handler: {e}", file=sys.stderr)
        print("Continuing with console-only logging", file=sys.stderr)

    # ========================================================================
    # CLEANUP OLD LOGS
    # ========================================================================

    try:
        deleted = cleanup_old_logs(days_to_keep=30)
        if deleted > 0:
            logger.debug(f"Cleaned up {deleted} old log file(s)")
    except Exception as e:
        logger.warning(f"Could not cleanup old logs: {e}")

    return logger


# ============================================================================
# DEFAULT LOGGER INSTANCE
# ============================================================================

# Create default logger for the application
logger = setup_logger("royal_research", level=logging.INFO)


# ============================================================================
# TESTING & DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    """
    Test the logging system with various log levels and scenarios.
    """

    print("="*70)
    print("ROYAL RESEARCH AUTOMATION - LOGGING SYSTEM TEST")
    print("="*70)
    print()

    # Show colorama status
    if COLORAMA_AVAILABLE:
        print(f"{Fore.GREEN}✅ Colorama available - Console output will be colored{Style.RESET_ALL}")
    else:
        print("⚠️  Colorama not available - Install with: pip install colorama")
    print()

    # Show log file location
    log_filename = f"research_{datetime.now().strftime('%Y-%m-%d')}.log"
    log_filepath = os.path.join(LOGS_DIR, log_filename)
    print(f"📁 Log file location: {log_filepath}")
    print()

    # Create test logger
    test_logger = setup_logger("test_module", level=logging.DEBUG)

    print("-"*70)
    print("Testing all log levels:")
    print("-"*70)
    print()

    # Test all log levels
    test_logger.debug("🔍 This is a DEBUG message - detailed diagnostic information")
    test_logger.info("ℹ️  This is an INFO message - general system information")
    test_logger.warning("⚠️  This is a WARNING message - something needs attention")
    test_logger.error("❌ This is an ERROR message - something went wrong")
    test_logger.critical("🚨 This is a CRITICAL message - system failure!")

    print()
    print("-"*70)
    print("Simulating real application scenarios:")
    print("-"*70)
    print()

    # Simulate real scenarios
    test_logger.info("Starting YouTube research automation system...")
    test_logger.debug("Loading configuration from config.py")
    test_logger.info("Configuration validated successfully")
    test_logger.debug("Initializing data collectors: Twitter, Reddit, YouTube")
    test_logger.warning("Twitter API rate limit: 450/500 requests remaining")
    test_logger.info("Collected 127 tweets from authority figures")
    test_logger.error("Reddit API connection timeout - retrying in 5 seconds")
    test_logger.info("Successfully connected to Reddit API")
    test_logger.debug("Processing 45 Reddit posts from r/SaintMeghanMarkle")
    test_logger.info("Research report generated successfully")
    test_logger.critical("SMTP authentication failed - cannot send email report!")

    print()
    print("-"*70)
    print("Testing Unicode/International text support:")
    print("-"*70)
    print()

    # Test international characters
    test_logger.info("Testing UTF-8: Royal Family 👑 Meghan Markle 🇬🇧")
    test_logger.info("French: Famille Royale Britannique")
    test_logger.info("German: Britische Königsfamilie")
    test_logger.info("Spanish: Familia Real Británica")

    print()
    print("="*70)
    print("✅ LOGGING SYSTEM TEST COMPLETE")
    print("="*70)
    print()
    print(f"Check the log file for detailed output: {log_filepath}")
    print()

    # Demonstrate log cleanup
    print("-"*70)
    print("Testing log cleanup function:")
    print("-"*70)
    deleted = cleanup_old_logs(days_to_keep=30)
    print(f"Deleted {deleted} log file(s) older than 30 days")
    print()

    # Show how to use in other modules
    print("-"*70)
    print("Usage in other modules:")
    print("-"*70)
    print()
    print("# Import the default logger:")
    print("from utils.logger import logger")
    print()
    print("# Or create a custom logger:")
    print("from utils.logger import setup_logger")
    print("logger = setup_logger(__name__, level=logging.DEBUG)")
    print()
    print("# Then use it:")
    print("logger.info('Starting data collection...')")
    print("logger.error('API call failed', exc_info=True)")
    print()
