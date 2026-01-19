"""
Twitter Data Collector

This module collects viral tweets about specified topics using Twitter API v2.
Identifies breaking news, trending topics, and viral angles for content creation.

Features:
- Searches tweets from the past 24 hours (configurable)
- Filters by minimum engagement threshold
- Calculates engagement metrics and rates
- Provides formatted output for AI analysis
- Automatic rate limit handling and retry logic
"""

import os
import sys
import time
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

import tweepy
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.rate_limiter import TWITTER_LIMITER


class TwitterCollector:
    """
    Collects and analyzes viral tweets using Twitter API v2.

    Features:
    - Searches recent tweets with engagement filtering
    - Calculates comprehensive engagement metrics
    - Identifies viral content and trending topics
    - Provides formatted output for AI content analysis
    """

    def __init__(
        self,
        bearer_token: str,
        min_engagement: int = 5000,
        max_results: int = 20
    ):
        """
        Initialize Twitter collector with API credentials.

        Args:
            bearer_token: Twitter API Bearer Token
            min_engagement: Minimum total engagement threshold (default: 5000)
            max_results: Maximum tweets to return per query (default: 20)

        Example:
            >>> collector = TwitterCollector(
            ...     bearer_token="your_token",
            ...     min_engagement=5000,
            ...     max_results=20
            ... )
        """
        self.bearer_token = bearer_token
        self.min_engagement = min_engagement
        self.max_results = max_results

        # Initialize Twitter API v2 client
        try:
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                wait_on_rate_limit=True  # Automatically wait on rate limits
            )
            logger.info(f"🐦 Initialized Twitter collector (min_engagement: {min_engagement})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twitter client: {e}")
            raise

    def _calculate_performance_indicator(self, engagement: int) -> str:
        """
        Calculate performance indicator emoji based on engagement level.

        Args:
            engagement: Total engagement count

        Returns:
            Performance indicator string with emoji
        """
        if engagement > 50000:
            return "🔥 MEGA VIRAL"
        elif engagement >= 20000:
            return "🚀 VIRAL"
        elif engagement >= 10000:
            return "📈 HIGH"
        else:
            return "✅ GOOD"

    def _sanitize_keyword(self, keyword: str) -> str:
        """
        Make keyword safe for Twitter API by removing operator words.

        Fixes issues like:
        - "car tuning and aftermarket parts" → "car tuning aftermarket parts"
        - Removes operator words (and, or, not) that cause API syntax errors

        Args:
            keyword: Original keyword

        Returns:
            Sanitized keyword safe for Twitter API
        """
        # Remove Twitter operator words that cause ambiguity
        operators = ['and', 'or', 'not', 'to', 'from']

        for op in operators:
            # Remove operator if it's a standalone word
            keyword = re.sub(rf'\b{op}\b', '', keyword, flags=re.IGNORECASE)

        # Clean up extra spaces
        keyword = re.sub(r'\s+', ' ', keyword).strip()

        # If keyword is now too short, quote original
        if len(keyword) < 3:
            return f'"{keyword}"'

        return keyword

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception)
    )
    def _search_tweets(
        self,
        keyword: str,
        hours_back: int
    ) -> Optional[tweepy.Response]:
        """
        Search tweets for a specific keyword with retry logic.

        Args:
            keyword: Search keyword
            hours_back: Hours to look back

        Returns:
            Tweepy response object or None if failed
        """
        try:
            # Calculate start time
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

            # Sanitize keyword for Twitter API
            safe_keyword = self._sanitize_keyword(keyword)

            # Build search query
            query = f"{safe_keyword} -is:retweet lang:en"

            logger.debug(f"🔍 Searching Twitter: '{query}' (since {start_time.isoformat()})")

            # Search tweets using API v2
            response = self.client.search_recent_tweets(
                query=query,
                start_time=start_time,
                max_results=min(100, self.max_results * 5),  # Get more to filter
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username', 'name', 'verified', 'public_metrics'],
                expansions=['author_id']
            )

            return response

        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter API error for '{keyword}': {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error searching '{keyword}': {e}")
            raise

    def collect(
        self,
        keywords: List[str],
        hours_back: int = 24
    ) -> Dict:
        """
        Collect viral tweets for specified keywords.

        Args:
            keywords: List of keywords to search for
            hours_back: Hours to look back (default: 24)

        Returns:
            Dictionary containing collected tweet data with structure:
            {
                "timestamp": "2026-01-18 15:30:00 UTC",
                "keywords": ["Meghan Markle", "Prince Harry"],
                "total_tweets_found": 45,
                "viral_tweets": [...]
            }

        Example:
            >>> data = collector.collect(
            ...     keywords=["Meghan Markle", "Prince Harry"],
            ...     hours_back=24
            ... )
        """
        logger.info(f"🐦 Collecting Twitter data for keywords: {', '.join(keywords)}")

        results = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "keywords": keywords,
            "total_tweets_found": 0,
            "viral_tweets": [],
            "rate_limited": False,
            "keywords_searched": 0,
            "keywords_failed": 0
        }

        for i, keyword in enumerate(keywords):
            # Check rate limiter before making request
            if not TWITTER_LIMITER.acquire():
                logger.warning(f"⚠️  Twitter rate limit reached at keyword {i+1}/{len(keywords)}, stopping")
                results['rate_limited'] = True
                results['keywords_failed'] = len(keywords) - i
                break

            try:
                logger.info(f"[{i+1}/{len(keywords)}] Searching Twitter for '{keyword}' (past {hours_back}h)...")

                # Search tweets
                response = self._search_tweets(keyword, hours_back)

                if not response or not response.data:
                    logger.info(f"ℹ️  No tweets found for '{keyword}'")
                    results["viral_tweets"].append({
                        "keyword": keyword,
                        "tweets": []
                    })
                    continue

                # Create user lookup dictionary
                users = {}
                if response.includes and 'users' in response.includes:
                    users = {user.id: user for user in response.includes['users']}

                # Process tweets
                processed_tweets = []

                for tweet in response.data:
                    try:
                        # Get author info
                        author = users.get(tweet.author_id)
                        if not author:
                            continue

                        # Extract public metrics
                        metrics = tweet.public_metrics or {}
                        like_count = metrics.get('like_count', 0)
                        retweet_count = metrics.get('retweet_count', 0)
                        reply_count = metrics.get('reply_count', 0)
                        quote_count = metrics.get('quote_count', 0)

                        # Calculate total engagement
                        total_engagement = (
                            like_count + retweet_count + reply_count + quote_count
                        )

                        # Filter by minimum engagement
                        if total_engagement < self.min_engagement:
                            continue

                        # Calculate hours ago
                        if tweet.created_at:
                            hours_ago = (
                                datetime.now(timezone.utc) - tweet.created_at
                            ).total_seconds() / 3600
                        else:
                            hours_ago = 0

                        # Calculate engagement rate
                        author_metrics = author.public_metrics or {}
                        author_followers = author_metrics.get('followers_count', 0)

                        if author_followers > 0:
                            engagement_rate = (total_engagement / author_followers) * 100
                        else:
                            engagement_rate = 0

                        # Build tweet data
                        tweet_data = {
                            "tweet_id": tweet.id,
                            "author_username": author.username,
                            "author_name": author.name,
                            "author_verified": getattr(author, 'verified', False),
                            "author_followers": author_followers,
                            "text": tweet.text,
                            "created_at": tweet.created_at.isoformat() if tweet.created_at else "",
                            "like_count": like_count,
                            "retweet_count": retweet_count,
                            "reply_count": reply_count,
                            "quote_count": quote_count,
                            "total_engagement": total_engagement,
                            "url": f"https://twitter.com/{author.username}/status/{tweet.id}",
                            "hours_ago": round(hours_ago, 2),
                            "engagement_rate": round(engagement_rate, 2),
                            "performance_indicator": self._calculate_performance_indicator(
                                total_engagement
                            )
                        }

                        processed_tweets.append(tweet_data)

                    except Exception as e:
                        logger.warning(f"⚠️  Error processing tweet {tweet.id}: {e}")
                        continue

                # Sort by total engagement (descending)
                processed_tweets.sort(key=lambda x: x['total_engagement'], reverse=True)

                # Limit to max_results
                processed_tweets = processed_tweets[:self.max_results]

                logger.info(
                    f"✅ Found {len(processed_tweets)} viral tweets for '{keyword}'"
                )

                results["viral_tweets"].append({
                    "keyword": keyword,
                    "tweets": processed_tweets
                })

                results["total_tweets_found"] += len(processed_tweets)
                results["keywords_searched"] += 1

                # Rate limiting - wait between keywords
                if keyword != keywords[-1]:
                    logger.debug("⏳ Waiting 2 seconds (rate limiting)...")
                    time.sleep(2)

            except tweepy.errors.BadRequest as e:
                # Twitter API syntax error - likely keyword issue
                logger.error(f"❌ Twitter API syntax error for '{keyword}': {e}")
                results["viral_tweets"].append({
                    "keyword": keyword,
                    "tweets": [],
                    "error": f"API syntax error: {str(e)}"
                })
                results["keywords_failed"] += 1
                continue
            except Exception as e:
                logger.error(f"❌ Error collecting tweets for '{keyword}': {e}")
                results["viral_tweets"].append({
                    "keyword": keyword,
                    "tweets": [],
                    "error": str(e)
                })
                results["keywords_failed"] += 1
                continue

        logger.info(
            f"✅ Twitter collection complete: {results['keywords_searched']}/{len(keywords)} keywords searched, "
            f"{results['total_tweets_found']} viral tweets found"
        )

        if results['rate_limited']:
            logger.warning(f"⚠️  Rate limited after {results['keywords_searched']} keywords")

        return results

    def format_for_prompt(self, data: Dict) -> str:
        """
        Format collected tweet data for AI prompt injection.

        Args:
            data: Dictionary returned from collect() method

        Returns:
            Formatted string with clear sections and visual separators

        Example output:
            ═══════════════════════════════════════════════════════════════════
            🐦 TWITTER VIRAL TWEETS ANALYSIS
            ═══════════════════════════════════════════════════════════════════
            [tweet data...]
        """
        output = []

        # Header
        output.append("═" * 70)
        output.append("🐦 TWITTER VIRAL TWEETS ANALYSIS")
        output.append("═" * 70)
        output.append(f"Collected: {data.get('timestamp', 'N/A')}")
        output.append(f"Keywords: {', '.join(data.get('keywords', []))}")
        output.append(f"Total Viral Tweets Found: {data.get('total_tweets_found', 0)}")
        output.append("")

        # Track top opportunities
        all_tweets = []

        # Process each keyword
        for keyword_data in data.get("viral_tweets", []):
            keyword = keyword_data.get("keyword", "Unknown")
            tweets = keyword_data.get("tweets", [])
            error = keyword_data.get("error")

            output.append("─" * 70)
            output.append(f"Keyword: \"{keyword}\"")
            output.append(f"Viral Tweets: {len(tweets)}")
            output.append("─" * 70)
            output.append("")

            if error:
                output.append(f"❌ ERROR: {error}")
                output.append("")
                continue

            if not tweets:
                output.append("ℹ️  No viral tweets found meeting engagement threshold")
                output.append("")
                continue

            # Show top 5 tweets per keyword
            for i, tweet in enumerate(tweets[:5], 1):
                all_tweets.append(tweet)

                output.append(f"{tweet['performance_indicator']}")
                output.append(f"Tweet #{i}")
                output.append("")

                # Author info
                verified_badge = "✓" if tweet['author_verified'] else ""
                output.append(
                    f"👤 Author: {tweet['author_name']} (@{tweet['author_username']}) {verified_badge}"
                )
                output.append(f"   Followers: {tweet['author_followers']:,}")
                output.append("")

                # Tweet text
                output.append(f"💬 Tweet:")
                output.append(f"   {tweet['text']}")
                output.append("")

                # Engagement metrics
                output.append(f"📊 Engagement:")
                output.append(f"   ❤️  Likes: {tweet['like_count']:,}")
                output.append(f"   🔄 Retweets: {tweet['retweet_count']:,}")
                output.append(f"   💭 Replies: {tweet['reply_count']:,}")
                output.append(f"   💬 Quotes: {tweet['quote_count']:,}")
                output.append(f"   📈 Total: {tweet['total_engagement']:,}")
                output.append(f"   ⚡ Rate: {tweet['engagement_rate']}%")
                output.append("")

                # Timing
                output.append(f"⏰ Posted: {tweet['hours_ago']}h ago")
                output.append("")

                # URL
                output.append(f"🔗 URL: {tweet['url']}")
                output.append("")

                # Suggested angle
                if tweet['total_engagement'] > 30000:
                    output.append("💡 SUGGESTED ANGLE: Breaking news/viral reaction video")
                elif tweet['total_engagement'] > 15000:
                    output.append("💡 SUGGESTED ANGLE: Trending topic analysis")
                else:
                    output.append("💡 SUGGESTED ANGLE: Commentary/discussion video")
                output.append("")

                output.append("─" * 70)
                output.append("")

        # Summary section
        output.append("═" * 70)
        output.append("🎯 VIDEO OPPORTUNITY SUMMARY")
        output.append("═" * 70)
        output.append("")

        if all_tweets:
            # Sort all tweets by engagement
            all_tweets.sort(key=lambda x: x['total_engagement'], reverse=True)

            output.append("🏆 TOP 3 VIRAL OPPORTUNITIES:")
            for i, tweet in enumerate(all_tweets[:3], 1):
                output.append(
                    f"   {i}. @{tweet['author_username']}: "
                    f"{tweet['total_engagement']:,} engagement "
                    f"({tweet['performance_indicator']})"
                )
                output.append(f"      \"{tweet['text'][:80]}...\"")
                output.append(f"      {tweet['url']}")
                output.append("")

            # Identify trending themes
            output.append("🔥 TRENDING THEMES:")
            output.append("   (Analyze tweet content to identify common topics)")
            output.append("")

            # Best posting times
            recent_tweets = [t for t in all_tweets if t['hours_ago'] < 6]
            if recent_tweets:
                output.append(f"⏱️  RECENT ACTIVITY: {len(recent_tweets)} viral tweets in last 6 hours")
                output.append("   → High engagement period detected")
            output.append("")

        else:
            output.append("ℹ️  No viral tweets found meeting the engagement threshold.")
            output.append(f"   Current threshold: {self.min_engagement:,} total engagement")
            output.append("")

        output.append("═" * 70)

        return "\n".join(output)


# ============================================================================
# TESTING & DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    """
    Test the Twitter collector with real API calls.
    """
    import config
    from utils.settings_manager import KeywordManager

    print("=" * 70)
    print("🐦 TESTING TWITTER COLLECTOR")
    print("=" * 70)
    print()

    # Load keywords from settings
    kw_mgr = KeywordManager()
    active_keywords = kw_mgr.get_active()

    if not active_keywords:
        print("⚠️  No active keywords found. Add some at http://localhost:5000/settings")
        exit(1)

    print(f"🔑 Using {len(active_keywords)} keywords: {', '.join(active_keywords)}")
    
    # Initialize collector
    try:
        collector = TwitterCollector(
            bearer_token=config.TWITTER_BEARER_TOKEN,
            min_engagement=1000, # Lowered threshold for quiet days
            max_results=10
        )
        print("✅ Twitter client initialized successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize Twitter client: {e}")
        print()
        print("Make sure you have:")
        print("1. Valid TWITTER_BEARER_TOKEN in your .env file")
        print("2. Twitter API v2 access enabled")
        sys.exit(1)

    print("🔄 Starting collection...")
    print("(This may take a few seconds)")
    print()

    try:
        # Collect data
        data = collector.collect(
            keywords=active_keywords,
            hours_back=24
        )

        # Show summary
        print()
        print("=" * 70)
        print("📊 RAW DATA SUMMARY")
        print("=" * 70)
        print(f"Total viral tweets: {data['total_tweets_found']}")
        print(f"Keywords searched: {data['keywords']}")
        print(f"Collection time: {data['timestamp']}")
        print()

        # Show formatted output
        print("=" * 70)
        print("📝 FORMATTED OUTPUT (For AI Prompts)")
        print("=" * 70)
        print()
        formatted = collector.format_for_prompt(data)
        print(formatted)

        print()
        print("=" * 70)
        print("✅ TWITTER COLLECTOR TEST COMPLETE")
        print("=" * 70)
        print()

    except Exception as e:
        print()
        print(f"❌ ERROR during collection: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
