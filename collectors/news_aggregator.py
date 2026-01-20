"""
News Aggregator

This module aggregates breaking news from NewsAPI and RSS feeds to identify
trending stories about Meghan Markle, Prince Harry, and the Royal Family.

Features:
- Collects from NewsAPI and UK tabloid RSS feeds
- Calculates relevance scores based on keywords and recency
- Deduplicates articles across sources
- Identifies trending topics
- Provides formatted output for AI analysis
"""

import os
import sys
import time
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from collections import Counter
import time as time_module

import feedparser
from newsapi import NewsApiClient
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger


# Default RSS feed sources
DEFAULT_RSS_FEEDS = {
    "Daily Mail Royals": "https://www.dailymail.co.uk/news/royals/index.rss",
    "The Sun Royals": "https://www.thesun.co.uk/topic/royal-family/feed/",
    "Express Royals": "https://www.express.co.uk/news/royal/rss",
}


class NewsAggregator:
    """
    Aggregates news from NewsAPI and RSS feeds for competitive intelligence.

    Features:
    - Dual-source collection (NewsAPI + RSS feeds)
    - Relevance scoring based on keywords and recency
    - Article deduplication
    - Trending topic identification
    - Formatted output for AI analysis
    """

    def __init__(
        self,
        news_api_key: str,
        rss_feeds: Optional[Dict[str, str]] = None
    ):
        """
        Initialize news aggregator.

        Args:
            news_api_key: NewsAPI key
            rss_feeds: Dict mapping source names to RSS feed URLs
                Default: UK tabloid royal news feeds

        Example:
            >>> aggregator = NewsAggregator(
            ...     news_api_key="your_key",
            ...     rss_feeds={"Daily Mail": "https://..."}
            ... )
        """
        self.news_api_key = news_api_key
        self.rss_feeds = rss_feeds or DEFAULT_RSS_FEEDS
        self.newsapi_requests = 0

        # Initialize NewsAPI client
        try:
            self.newsapi = NewsApiClient(api_key=news_api_key)
            logger.info(
                f"📰 Initialized news aggregator with NewsAPI + {len(self.rss_feeds)} RSS feeds"
            )
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize NewsAPI: {e}")
            self.newsapi = None

    def _calculate_relevance_score(
        self,
        title: str,
        description: str,
        source: str,
        hours_ago: float,
        keywords: List[str]
    ) -> float:
        """
        Calculate relevance score for an article.

        Args:
            title: Article title
            description: Article description
            source: Publication name
            hours_ago: Hours since publication
            keywords: List of search keywords

        Returns:
            Relevance score (0-10)
        """
        score = 5.0  # Base score

        title_lower = title.lower()
        desc_lower = description.lower()

        # Keyword mentions in title
        for keyword in keywords:
            if keyword.lower() in title_lower:
                score += 1.0

        # Keyword mentions in description
        for keyword in keywords:
            if keyword.lower() in desc_lower:
                score += 0.5

        # Recency bonus
        if hours_ago < 6:
            score += 2.0
        elif hours_ago < 12:
            score += 1.0
        elif hours_ago < 24:
            score += 0.5

        # Tabloid bonus
        if "daily mail" in source.lower() or "the sun" in source.lower():
            score += 1.0

        return min(score, 10.0)  # Cap at 10.0

    def _generate_article_id(self, url: str) -> str:
        """Generate unique article ID from URL."""
        return hashlib.md5(url.encode()).hexdigest()[:16]

    @retry(
        wait=wait_fixed(3),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(Exception)
    )
    def _collect_newsapi(
        self,
        keywords: List[str],
        hours_back: int
    ) -> List[Dict]:
        """
        Collect articles from NewsAPI.

        Args:
            keywords: List of keywords to search
            hours_back: Hours to look back

        Returns:
            List of article dictionaries
        """
        if not self.newsapi:
            logger.info("ℹ️  NewsAPI not available, skipping...")
            return []

        articles = []
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        end_time = datetime.now(timezone.utc)

        for keyword in keywords:
            try:
                logger.info(f"Searching NewsAPI for '{keyword}'...")

                response = self.newsapi.get_everything(
                    q=keyword,
                    language='en',
                    from_param=start_time.strftime('%Y-%m-%d'),
                    to=end_time.strftime('%Y-%m-%d'),
                    sort_by='publishedAt',
                    page_size=20
                )

                self.newsapi_requests += 1

                for article in response.get('articles', []):
                    try:
                        # Parse published time
                        published_str = article.get('publishedAt', '')
                        if published_str:
                            published_at = datetime.fromisoformat(
                                published_str.replace('Z', '+00:00')
                            )
                        else:
                            continue

                        # Calculate hours ago
                        hours_ago = (
                            datetime.now(timezone.utc) - published_at
                        ).total_seconds() / 3600

                        url = article.get('url')
                        if not url:
                            continue

                        articles.append({
                            'article_id': self._generate_article_id(url),
                            'title': article.get('title', 'Untitled'),
                            'source': article.get('source', {}).get('name', 'Unknown'),
                            'author': article.get('author', 'Unknown'),
                            'published_at': published_at.isoformat(),
                            'url': url,
                            'description': (article.get('description') or '')[:200],
                            'content': (article.get('content') or '')[:300],
                            'source_type': 'NewsAPI',
                            'hours_ago': round(hours_ago, 1),
                            'matched_keywords': [keyword]
                        })

                    except Exception as e:
                        logger.warning(f"⚠️  Error processing NewsAPI article: {e}")
                        continue

                # Rate limiting
                if keyword != keywords[-1]:
                    time.sleep(1)

            except Exception as e:
                logger.error(f"❌ NewsAPI error for '{keyword}': {e}")
                continue

        logger.info(f"✅ Found {len(articles)} articles from NewsAPI")
        return articles

    @retry(
        wait=wait_fixed(3),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(Exception)
    )
    def _collect_rss(
        self,
        keywords: List[str],
        hours_back: int
    ) -> List[Dict]:
        """
        Collect articles from RSS feeds.

        Args:
            keywords: List of keywords to match
            hours_back: Hours to look back

        Returns:
            List of article dictionaries
        """
        articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        for feed_name, feed_url in self.rss_feeds.items():
            try:
                logger.info(f"Fetching RSS feed: {feed_name}...")

                feed = feedparser.parse(feed_url)

                for entry in feed.entries:
                    try:
                        # Parse published time
                        if hasattr(entry, 'published_parsed'):
                            published_tuple = entry.published_parsed
                        elif hasattr(entry, 'updated_parsed'):
                            published_tuple = entry.updated_parsed
                        else:
                            continue

                        published_at = datetime(*published_tuple[:6], tzinfo=timezone.utc)

                        # Filter by time
                        if published_at < cutoff_time:
                            continue

                        # Get title and check for keyword match
                        title = entry.get('title', '')
                        description = entry.get('summary', '') or entry.get('description', '')

                        # Check if any keyword matches
                        matched_keywords = []
                        title_lower = title.lower()
                        desc_lower = description.lower()

                        for keyword in keywords:
                            if keyword.lower() in title_lower or keyword.lower() in desc_lower:
                                matched_keywords.append(keyword)

                        if not matched_keywords:
                            continue

                        # Get URL
                        url = entry.get('link', '')
                        if not url:
                            continue

                        # Calculate hours ago
                        hours_ago = (
                            datetime.now(timezone.utc) - published_at
                        ).total_seconds() / 3600

                        articles.append({
                            'article_id': self._generate_article_id(url),
                            'title': title,
                            'source': feed_name.replace(' Royals', ''),
                            'author': entry.get('author', 'Unknown'),
                            'published_at': published_at.isoformat(),
                            'url': url,
                            'description': description[:200],
                            'content': description[:300],
                            'source_type': 'RSS',
                            'hours_ago': round(hours_ago, 1),
                            'matched_keywords': matched_keywords
                        })

                    except Exception as e:
                        logger.warning(f"⚠️  Error processing RSS entry: {e}")
                        continue

                # Rate limiting
                time.sleep(2)

            except Exception as e:
                logger.error(f"❌ RSS feed error for {feed_name}: {e}")
                continue

        logger.info(f"✅ Found {len(articles)} articles from RSS feeds")
        return articles

    def collect(
        self,
        keywords: List[str],
        hours_back: int = 24,
        max_articles: int = 15
    ) -> Dict:
        """
        Collect news articles from NewsAPI and RSS feeds.

        Args:
            keywords: List of keywords to search
            hours_back: Hours to look back (default: 24)
            max_articles: Maximum articles to return (default: 15)

        Returns:
            Dictionary containing aggregated news data

        Example:
            >>> data = aggregator.collect(
            ...     keywords=["Meghan Markle", "Prince Harry"],
            ...     hours_back=24,
            ...     max_articles=15
            ... )
        """
        logger.info(f"📰 Collecting news for keywords: {', '.join(keywords)}")

        # Collect from both sources
        newsapi_articles = self._collect_newsapi(keywords, hours_back)
        rss_articles = self._collect_rss(keywords, hours_back)

        # Combine and deduplicate
        all_articles = newsapi_articles + rss_articles

        # Deduplicate by article_id (URL hash)
        seen_ids = set()
        deduped_articles = []

        for article in all_articles:
            if article['article_id'] not in seen_ids:
                seen_ids.add(article['article_id'])
                deduped_articles.append(article)

        duplicates_removed = len(all_articles) - len(deduped_articles)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate articles")

        # Calculate relevance scores
        for article in deduped_articles:
            article['relevance_score'] = self._calculate_relevance_score(
                article['title'],
                article['description'],
                article['source'],
                article['hours_ago'],
                keywords
            )

        # Sort by relevance score
        deduped_articles.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Limit to max_articles
        final_articles = deduped_articles[:max_articles]

        # Count sources
        source_counts = Counter(a['source_type'] for a in final_articles)
        source_names = Counter(a['source'] for a in final_articles)

        # Extract trending topics (frequent words in titles)
        all_titles = ' '.join(a['title'] for a in final_articles)
        words = all_titles.split()
        word_counts = Counter(
            w for w in words
            if len(w) > 4 and w[0].isupper()  # Capitalized words longer than 4 chars
        )
        trending_topics = [word for word, count in word_counts.most_common(5)]

        results = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "monitoring_window": f"{hours_back} hours",
            "keywords": keywords,
            "total_articles": len(final_articles),
            "sources": {
                "NewsAPI": source_counts.get('NewsAPI', 0),
                "RSS": source_counts.get('RSS', 0)
            },
            "articles": final_articles,
            "trending_topics": trending_topics,
            "top_sources": source_names.most_common(5)
        }

        logger.info(
            f"NewsAPI requests used: {self.newsapi_requests}/100 (free tier)"
        )

        logger.info(
            f"✅ News aggregation complete: {len(final_articles)} articles "
            f"from {len(source_names)} sources"
        )

        return results

    def format_for_prompt(self, data: Dict) -> str:
        """
        Format collected news for AI prompt injection.

        Args:
            data: Dictionary returned from collect() method

        Returns:
            Formatted string with clear sections and visual separators
        """
        output = []

        # Header
        output.append("═" * 70)
        output.append("📰 NEWS AGGREGATION REPORT")
        output.append("═" * 70)
        output.append(f"Collected: {data.get('timestamp', 'N/A')}")
        output.append(f"Monitoring Window: {data.get('monitoring_window', 'N/A')}")
        output.append(f"Keywords: {', '.join(data.get('keywords', []))}")
        output.append(f"Total Articles: {data.get('total_articles', 0)}")
        output.append("")

        # Source breakdown
        sources = data.get('sources', {})
        output.append(f"📊 Sources: NewsAPI ({sources.get('NewsAPI', 0)}) | RSS ({sources.get('RSS', 0)})")
        output.append("")

        # Articles
        articles = data.get('articles', [])

        if not articles:
            output.append("ℹ️  No articles found matching criteria")
            output.append("")
            return "\n".join(output)

        # Freshness analysis
        very_fresh = len([a for a in articles if a['hours_ago'] < 6])
        fresh = len([a for a in articles if 6 <= a['hours_ago'] < 12])
        recent = len([a for a in articles if 12 <= a['hours_ago'] < 24])

        output.append(f"⏰ Freshness: <6h ({very_fresh}) | 6-12h ({fresh}) | 12-24h ({recent})")
        output.append("")

        output.append("─" * 70)
        output.append("📰 ARTICLES (Sorted by Relevance)")
        output.append("─" * 70)
        output.append("")

        for i, article in enumerate(articles, 1):
            # Relevance indicator
            score = article.get('relevance_score', 0)
            if score > 8.0:
                indicator = "🔥 HIGH"
            elif score >= 6.0:
                indicator = "🔴 MEDIUM"
            else:
                indicator = "⚪ LOW"

            output.append(f"{indicator} | Relevance: {score:.1f}")
            output.append(f"#{i}. {article['title']}")
            output.append("")

            output.append(f"📍 Source: {article['source']} | Author: {article['author']}")
            output.append(f"⏰ Published: {article['hours_ago']:.1f}h ago")
            output.append(f"🔑 Matched: {', '.join(article['matched_keywords'])}")
            output.append("")

            if article['description']:
                output.append(f"📝 {article['description']}")
                output.append("")

            output.append(f"🔗 {article['url']}")
            output.append("")

            # Video angle suggestion
            if score > 8.0:
                output.append("💡 VIDEO ANGLE: Breaking news reaction - strike while it's hot!")
            elif score >= 7.0:
                output.append("💡 VIDEO ANGLE: Trending topic analysis - ride the wave")
            else:
                output.append("💡 VIDEO ANGLE: News roundup mention")
            output.append("")

            output.append("─" * 70)
            output.append("")

        # Summary section
        output.append("═" * 70)
        output.append("🎯 VIDEO OPPORTUNITIES")
        output.append("═" * 70)
        output.append("")

        # Top 3 opportunities
        output.append("🏆 TOP 3 STORIES:")
        for i, article in enumerate(articles[:3], 1):
            output.append(
                f"   {i}. {article['source']}: \"{article['title'][:60]}...\""
            )
            output.append(f"      Relevance: {article['relevance_score']:.1f} | {article['hours_ago']:.1f}h ago")
            output.append("")

        # Trending topics
        trending = data.get('trending_topics', [])
        if trending:
            output.append("🔥 TRENDING TOPICS:")
            output.append(f"   {', '.join(trending)}")
            output.append("")

        # Top sources
        top_sources = data.get('top_sources', [])
        if top_sources:
            output.append("📊 TOP SOURCES:")
            for source, count in top_sources[:3]:
                output.append(f"   • {source}: {count} articles")
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
    Test the news aggregator with real API calls.
    """
    import config
    from utils.settings_manager import KeywordManager

    print("=" * 70)
    print("📰 TESTING NEWS AGGREGATOR")
    print("=" * 70)
    print()
    
    # Load keywords from settings
    kw_mgr = KeywordManager()
    active_keywords = kw_mgr.get_active()

    if not active_keywords:
        print("⚠️  No active keywords found. Add some at http://localhost:5000/settings")
        exit(1)

    print(f"🔑 Using {len(active_keywords)} keywords: {', '.join(active_keywords)}")
    
    # Initialize aggregator
    try:
        rss_feeds = {
            "Daily Mail Royals": "https://www.dailymail.co.uk/news/royals/index.rss",
            "The Sun Royals": "https://www.thesun.co.uk/topic/royal-family/feed/",
            "Express Royals": "https://www.express.co.uk/news/royal/rss",
        }

        aggregator = NewsAggregator(
            news_api_key=config.NEWSAPI_KEY,
            rss_feeds=rss_feeds
        )
        print("✅ News aggregator initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize news aggregator: {e}")
        sys.exit(1)

    print(f"🔍 Collecting news...")
    print("(This may take a few seconds)")
    print()

    try:
        # Collect data
        data = aggregator.collect(
            keywords=active_keywords, 
            hours_back=24,
            max_articles=15
        )

        # Show summary
        print()
        print("=" * 70)
        print("📊 RAW DATA SUMMARY")
        print("=" * 70)
        print(f"Total articles: {data['total_articles']}")
        print(f"NewsAPI articles: {data['sources']['NewsAPI']}")
        print(f"RSS articles: {data['sources']['RSS']}")
        print(f"Top sources: {data['top_sources'][:3]}")
        print()

        if data['articles']:
            article = data['articles'][0]
            print("Top article:")
            print(f"  Title: {article['title']}")
            print(f"  Source: {article['source']}")
            print(f"  Relevance: {article['relevance_score']:.1f}")
            print(f"  Published: {article['hours_ago']:.1f}h ago")
            print()

        # Show formatted output
        print("=" * 70)
        print("📝 FORMATTED OUTPUT (For AI Prompts)")
        print("=" * 70)
        print()
        formatted = aggregator.format_for_prompt(data)
        print(formatted)

        print()
        print("=" * 70)
        print("✅ NEWS AGGREGATOR TEST COMPLETE")
        print("=" * 70)
        print()
        print("USAGE IN YOUR APPLICATION:")
        print()
        print("from collectors.news_aggregator import NewsAggregator")
        print("from config import NEWSAPI_KEY")
        print()
        print("aggregator = NewsAggregator(NEWSAPI_KEY)")
        print("data = aggregator.collect(keywords=['Meghan Markle'], hours_back=24)")
        print("formatted_text = aggregator.format_for_prompt(data)")
        print()

    except Exception as e:
        print()
        print(f"❌ ERROR during collection: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
