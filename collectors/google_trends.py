"""
Google Trends Data Collector

This module collects trending search data from Google Trends to identify:
- Breakout queries (5000%+ increase)
- Rising queries (100% to 5000% increase)
- Top related queries
- Interest over time

No API key required - uses pytrends library for web scraping.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

from pytrends.request import TrendReq
from utils.logger import logger
from utils.rate_limiter import GOOGLE_TRENDS_LIMITER



from utils.system_config import SYSTEM_CONFIG

class GoogleTrendsCollector:
    """
    Collects and analyzes Google Trends data for specified keywords.

    Features:
    - Tracks breakout and rising search queries
    - Identifies trending topics in real-time
    - Provides formatted output for AI analysis
    - Automatic retry with exponential backoff
    - Rate limiting to avoid blocks
    """

    def __init__(self, keywords: List[str], time_window_hours: int = 24):
        """
        Initialize Google Trends collector.

        Args:
            keywords: List of keywords to track (e.g., ["Meghan Markle", "Prince Harry"])
            time_window_hours: Hours to look back for trends (default: 24)

        Example:
            >>> collector = GoogleTrendsCollector(["Meghan Markle", "Prince Harry"])
            >>> data = collector.collect()
        """
        self.keywords = keywords
        self.time_window_hours = time_window_hours

        # Initialize pytrends with timeout
        # Note: Removed retries/backoff_factor due to urllib3 compatibility issues
        # Retry logic is handled manually in _collect_keyword method
        self.pytrends = TrendReq(
            hl='en-US',
            tz=0,  # UTC timezone
            timeout=(10, 25)  # (connect, read) timeout in seconds
        )

        logger.info(f"📊 Initialized Google Trends collector for {len(keywords)} keywords")

    def collect(self) -> Dict:
        """
        Collect Google Trends data for all configured keywords.

        Returns:
            Dictionary containing trends data for each keyword with structure:
            {
                "timestamp": "2026-01-18T12:34:56",
                "keywords": {
                    "Meghan Markle": {
                        "rising_queries": [...],
                        "top_queries": [...],
                        "has_breakout": True/False
                    }
                },
                "total_breakouts": 5,
                "total_rising": 12
            }

        Raises:
            Exception: If all keyword collections fail
        """
        logger.info(f"🔍 Collecting Google Trends data for: {', '.join(self.keywords)}")

        results = {
            "timestamp": datetime.now().isoformat(),
            "keywords": {},
            "total_breakouts": 0,
            "total_rising": 0
        }

        successful_collections = 0
        
        # Get settings
        fail_fast = SYSTEM_CONFIG.get('collection_settings.google_trends_fail_fast', True)

        # Process each keyword
        for i, keyword in enumerate(self.keywords):
            # Check rate limiter before making request
            if not GOOGLE_TRENDS_LIMITER.acquire():
                logger.warning(f"⚠️  Rate limit reached at keyword {i+1}/{len(self.keywords)}, stopping")
                break

            try:
                keyword_data = self._collect_keyword(keyword)

                if keyword_data:
                    results["keywords"][keyword] = keyword_data
                    successful_collections += 1

                    # Count breakouts and rising
                    if keyword_data.get("has_breakout"):
                        breakout_count = len([q for q in keyword_data.get("rising_queries", [])
                                             if q.get("value") == "Breakout"])
                        results["total_breakouts"] += breakout_count

                    rising_count = len([q for q in keyword_data.get("rising_queries", [])
                                       if q.get("value") != "Breakout"])
                    results["total_rising"] += rising_count

                    logger.info(
                        f"✅ [{i+1}/{len(self.keywords)}] Collected trends for '{keyword}': "
                        f"{len(keyword_data.get('rising_queries', []))} rising, "
                        f"{len(keyword_data.get('top_queries', []))} top"
                    )

                # Rate limiting - wait between keywords
                if keyword != self.keywords[-1]:  # Don't wait after last keyword
                    logger.debug(f"⏳ Waiting 2 seconds before next keyword (rate limiting)...")
                    time.sleep(2)

            except Exception as e:
                error_msg = str(e)

                # Check for rate limit errors
                if '429' in error_msg or 'quota' in error_msg.lower() or 'rate' in error_msg.lower():
                    if fail_fast:
                        logger.error(f"❌ Rate limited at keyword '{keyword}', stopping collection (fail-fast enabled)")
                        break
                    else:
                        logger.warning(f"⚠️ Rate limited at keyword '{keyword}', continuing to next...")
                else:
                    logger.error(f"❌ Error collecting trends for '{keyword}': {error_msg}")
                    continue

        # Check if we got any data
        if successful_collections == 0:
            error_msg = "Failed to collect data for any keywords"
            logger.error(f"❌ {error_msg}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "keywords": {}
            }

        logger.info(
            f"✅ Google Trends collection complete: "
            f"{successful_collections}/{len(self.keywords)} keywords successful, "
            f"{results['total_breakouts']} breakouts, {results['total_rising']} rising"
        )

        return results

    def _collect_keyword(self, keyword: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Collect trends data for a single keyword with retry logic.

        Args:
            keyword: Keyword to collect data for
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with rising_queries, top_queries, and has_breakout flag
            Returns None if collection fails
        """
        # Determine timeframe based on time_window_hours
        if self.time_window_hours <= 24:
            timeframe = 'now 1-d'  # Past 24 hours
        elif self.time_window_hours <= 168:  # 7 days
            timeframe = 'now 7-d'
        else:
            timeframe = 'today 1-m'  # Past month

        fail_fast = SYSTEM_CONFIG.get('collection_settings.google_trends_fail_fast', True)

        for attempt in range(max_retries):
            try:
                logger.debug(f"🔄 Attempt {attempt + 1}/{max_retries} for keyword: '{keyword}'")

                # Build payload for this keyword
                self.pytrends.build_payload(
                    kw_list=[keyword],
                    cat=0,  # All categories
                    timeframe=timeframe,
                    geo='',  # Worldwide
                    gprop=''  # Web search
                )

                # Get related queries
                related_queries = self.pytrends.related_queries()

                # Extract data for this keyword
                keyword_queries = related_queries.get(keyword, {})

                if not keyword_queries:
                    logger.warning(f"⚠️  No related queries found for '{keyword}'")
                    return None

                # Process rising queries
                rising_queries = []
                rising_df = keyword_queries.get('rising')

                if rising_df is not None and not rising_df.empty:
                    for _, row in rising_df.head(10).iterrows():
                        query_text = row.get('query', '')
                        value = row.get('value', 0)

                        # Handle "Breakout" designation
                        if isinstance(value, str) and value.lower() == 'breakout':
                            value_formatted = "Breakout"
                        else:
                            value_formatted = f"+{value}%" if isinstance(value, (int, float)) else str(value)

                        rising_queries.append({
                            "query": query_text,
                            "value": value_formatted
                        })

                # Process top queries
                top_queries = []
                top_df = keyword_queries.get('top')

                if top_df is not None and not top_df.empty:
                    for _, row in top_df.head(10).iterrows():
                        query_text = row.get('query', '')
                        value = row.get('value', 0)

                        top_queries.append({
                            "query": query_text,
                            "value": int(value) if isinstance(value, (int, float)) else value
                        })

                # Check for breakout queries
                has_breakout = any(
                    q.get('value') == 'Breakout'
                    for q in rising_queries
                )

                return {
                    "rising_queries": rising_queries,
                    "top_queries": top_queries,
                    "has_breakout": has_breakout
                }

            except Exception as e:
                error_msg = str(e).lower()
                
                # FAIL-FAST on rate limits (don't retry)
                if fail_fast and ('429' in error_msg or 'quota' in error_msg or 'rate' in error_msg):
                    logger.warning(f"⚠️ Rate limited for '{keyword}' - skipping (fail-fast enabled)")
                    # Return a special "rate_limited" status so the caller knows what happened
                    return {
                        'status': 'rate_limited',
                        'rising_queries': [],
                        'top_queries': [],
                        'has_breakout': False
                    }

                wait_time = (2 ** attempt)  # Exponential backoff: 1, 2, 4 seconds

                if attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️  Error on attempt {attempt + 1} for '{keyword}': {str(e)}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed all {max_retries} attempts for '{keyword}': {str(e)}")
                    return None

        return None

    def format_for_prompt(self, data: Dict) -> str:
        """
        Format collected trends data into human-readable text for AI analysis.

        Args:
            data: Dictionary returned from collect() method

        Returns:
            Formatted string with clear sections and visual separators

        Example output:
            ═══════════════════════════════════════════════════════════════════
            📊 GOOGLE TRENDS ANALYSIS (Past 24 Hours)
            ═══════════════════════════════════════════════════════════════════
            [keyword data...]
        """
        output = []

        # Header
        output.append("═" * 70)
        output.append(f"📊 GOOGLE TRENDS ANALYSIS (Past {self.time_window_hours} Hours)")
        output.append("═" * 70)
        output.append(f"Collected: {data.get('timestamp', 'N/A')}")
        output.append("")

        # Check for errors
        if "error" in data:
            output.append(f"❌ ERROR: {data['error']}")
            return "\n".join(output)

        # Summary
        output.append(f"📈 SUMMARY:")
        output.append(f"   Total Breakout Queries: {data.get('total_breakouts', 0)}")
        output.append(f"   Total Rising Queries: {data.get('total_rising', 0)}")
        output.append("")

        # Process each keyword
        keywords_data = data.get("keywords", {})

        for keyword, keyword_data in keywords_data.items():
            output.append("─" * 70)
            output.append(f"Keyword: \"{keyword}\"")
            output.append("─" * 70)
            output.append("")

            # Breakout queries
            rising_queries = keyword_data.get("rising_queries", [])
            breakout_queries = [q for q in rising_queries if q.get("value") == "Breakout"]

            if breakout_queries:
                output.append("🔥 BREAKOUT QUERIES (5000%+ increase):")
                for i, query in enumerate(breakout_queries, 1):
                    output.append(f"   {i}. \"{query['query']}\" - {query['value']}")
                output.append("")

            # Rising queries (non-breakout)
            rising_non_breakout = [q for q in rising_queries if q.get("value") != "Breakout"]

            if rising_non_breakout:
                output.append("📈 RISING QUERIES (+100% to +5000%):")
                for i, query in enumerate(rising_non_breakout[:5], 1):  # Top 5
                    output.append(f"   {i}. \"{query['query']}\" - {query['value']}")
                output.append("")

            # Top queries
            top_queries = keyword_data.get("top_queries", [])

            if top_queries:
                output.append("🔝 TOP RELATED QUERIES:")
                for i, query in enumerate(top_queries[:5], 1):  # Top 5
                    output.append(f"   {i}. \"{query['query']}\"")
                output.append("")

        # Video opportunity assessment
        output.append("═" * 70)
        output.append("🎥 VIDEO OPPORTUNITY ASSESSMENT")
        output.append("═" * 70)
        output.append("")

        # Collect all breakout queries across keywords
        all_breakouts = []
        all_top_rising = []

        for keyword, keyword_data in keywords_data.items():
            rising_queries = keyword_data.get("rising_queries", [])

            for query in rising_queries:
                if query.get("value") == "Breakout":
                    all_breakouts.append(f"\"{query['query']}\" (from: {keyword})")
                elif query.get("value") != "Breakout":
                    # Extract numeric value for sorting
                    value_str = query.get("value", "0")
                    try:
                        numeric_value = int(value_str.replace("+", "").replace("%", ""))
                    except (ValueError, AttributeError):
                        numeric_value = 0

                    if numeric_value >= 200:  # High rising threshold
                        all_top_rising.append(
                            f"\"{query['query']}\" - {query['value']} (from: {keyword})"
                        )

        # Display opportunities
        if all_breakouts:
            output.append("✅ STRONG OPPORTUNITIES (Breakout Queries):")
            for breakout in all_breakouts[:5]:
                output.append(f"   • {breakout}")
            output.append("")

        if all_top_rising:
            output.append("⚠️  MODERATE OPPORTUNITIES (High Rising Queries):")
            for rising in all_top_rising[:5]:
                output.append(f"   • {rising}")
            output.append("")

        if not all_breakouts and not all_top_rising:
            output.append("ℹ️  No significant breakout or high-rising opportunities detected.")
            output.append("   Consider monitoring trending topics or waiting for new developments.")
            output.append("")

        output.append("═" * 70)

        return "\n".join(output)


# ============================================================================
# TESTING & DEMONSTRATION
# ============================================================================

# ============================================================================
# TESTING & DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    """
    Test the Google Trends collector with real keywords.
    """
    import config
    from utils.settings_manager import KeywordManager

    print("=" * 70)
    print("TESTING GOOGLE TRENDS COLLECTOR")
    print("=" * 70)
    print()

    # Load keywords from settings
    kw_mgr = KeywordManager()
    active_keywords = kw_mgr.get_active()

    if not active_keywords:
        print("⚠️  No active keywords found. Add some at http://localhost:5000/settings")
        exit(1)

    print(f"🔑 Tracking {len(active_keywords)} keywords: {', '.join(active_keywords)}")
    print()

    collector = GoogleTrendsCollector(
        keywords=active_keywords,
        time_window_hours=config.TIME_WINDOW_HOURS
    )

    # Collect data
    print("🔄 Starting data collection...")
    print("(This may take a few seconds due to rate limiting)")
    print()

    data = collector.collect()

    # Show formatted output
    print()
    print("=" * 70)
    print("FORMATTED OUTPUT (For AI Prompt Injection)")
    print("=" * 70)
    print()

    formatted = collector.format_for_prompt(data)
    print(formatted)

    # Show raw data structure
    print()
    print("=" * 70)
    print("RAW DATA STRUCTURE (JSON)")
    print("=" * 70)
    print()
    print(json.dumps(data, indent=2, default=str))
    print()

    # Usage example
    print("=" * 70)
    print("USAGE IN YOUR APPLICATION")
    print("=" * 70)
    print()
    print("from collectors.google_trends import GoogleTrendsCollector")
    print("from config import RESEARCH_KEYWORDS, TIME_WINDOW_HOURS")
    print()
    print("# Initialize")
    print("collector = GoogleTrendsCollector(RESEARCH_KEYWORDS, TIME_WINDOW_HOURS)")
    print()
    print("# Collect data")
    print("trends_data = collector.collect()")
    print()
    print("# Get formatted text for AI analysis")
    print("formatted_text = collector.format_for_prompt(trends_data)")
    print()
    print("# Use in your AI prompt")
    print("prompt = f'Analyze these trends and suggest video ideas:\\n{formatted_text}'")
    print()
