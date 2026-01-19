import os
from dotenv import load_dotenv
from typing import Dict
from pathlib import Path

# Load environment variables from .env file in the same directory as this script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True, encoding='utf-8')


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


# ============================================================================
# ENVIRONMENT VARIABLES (Loaded from .env)
# ============================================================================

# Twitter API
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Reddit API
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# YouTube API
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# News API
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Anthropic API (for Claude)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Email Configuration
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Scheduling Configuration
RESEARCH_TIME = os.getenv("RESEARCH_TIME", "06:00")
TIMEZONE = os.getenv("TIMEZONE", "Europe/London")


# ============================================================================
# APPLICATION CONSTANTS
# ============================================================================

# Research Keywords - Topics to monitor
RESEARCH_KEYWORDS = [
    "Meghan Markle",
    "Prince Harry",
    "Archewell Foundation",
    "Royal Family"
]

# Authority Figures - Key voices to track
AUTHORITY_FIGURES = [
    "Tom Bower",
    "Piers Morgan",
    "Lady Colin Campbell"
]

# Competitor YouTube Channels
COMPETITOR_CHANNELS: Dict[str, str] = {
    "Jessica Talks Tea": "UCxxxxxxx",
    "Lena Exposed": "UCyyyyyyy"
}

# Reddit Communities to Monitor
SUBREDDITS = [
    "SaintMeghanMarkle"
]

# Data Collection Parameters
TIME_WINDOW_HOURS = 24  # How far back to look for content
MIN_TWITTER_ENGAGEMENT = 5000  # Minimum likes/retweets to consider
MIN_REDDIT_UPVOTES = 200  # Minimum upvotes to consider
REDDIT_MIN_UPVOTES = 200  # Alias for backward compatibility
REDDIT_SUBREDDIT = "SaintMeghanMarkle"  # Primary subreddit to monitor
NEWS_MAX_ARTICLES = 10  # Maximum articles per keyword from NewsAPI

# File Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
REPORTS_DIR = os.path.join(DATA_DIR, "research_reports")
LOGS_DIR = os.path.join(DATA_DIR, "logs")


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config() -> None:
    """
    Validates that all required environment variables are set.
    Raises ConfigurationError with helpful messages if any are missing.
    """
    missing_vars = []

    # Required API Keys
    required_vars = {
        "TWITTER_BEARER_TOKEN": TWITTER_BEARER_TOKEN,
        "REDDIT_CLIENT_ID": REDDIT_CLIENT_ID,
        "REDDIT_CLIENT_SECRET": REDDIT_CLIENT_SECRET,
        "REDDIT_USER_AGENT": REDDIT_USER_AGENT,
        "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
        "NEWSAPI_KEY": NEWSAPI_KEY,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
        "SMTP_EMAIL": SMTP_EMAIL,
        "SMTP_PASSWORD": SMTP_PASSWORD,
        "RECIPIENT_EMAIL": RECIPIENT_EMAIL,
    }

    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)

    if missing_vars:
        error_message = (
            "\n" + "="*70 + "\n"
            "CONFIGURATION ERROR: Missing Required Environment Variables\n"
            + "="*70 + "\n\n"
            "The following environment variables are not set:\n\n"
        )

        for var in missing_vars:
            error_message += f"  ❌ {var}\n"

        error_message += (
            "\n" + "-"*70 + "\n"
            "How to fix:\n"
            "1. Copy .env.example to .env\n"
            "2. Fill in all required API keys and credentials\n"
            "3. Restart the application\n"
            + "-"*70 + "\n"
        )

        raise ConfigurationError(error_message)

    print("✅ Configuration validated successfully!")
    print(f"📊 Monitoring keywords: {', '.join(RESEARCH_KEYWORDS)}")
    print(f"⏰ Scheduled research time: {RESEARCH_TIME} ({TIMEZONE})")
    print(f"📧 Reports will be sent to: {RECIPIENT_EMAIL}")


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Test configuration when run directly
    try:
        validate_config()
    except ConfigurationError as e:
        print(e)
