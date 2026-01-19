"""
Reddit Web Scraper

This module scrapes Reddit (without API) to collect trending discussions,
timelines, evidence, and speculation from r/SaintMeghanMarkle for content research.

Features:
- No API required - uses web scraping with requests + BeautifulSoup
- Auto-detects post types (Timeline, Evidence, News, Speculation, Discussion)
- Calculates video potential based on engagement
- Provides formatted output for AI analysis
"""

import os
import sys
import time
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger


class RedditScraper:
    """
    Scrapes Reddit to collect trending discussions and evidence-based posts.

    Features:
    - Web scraping without API (uses old.reddit.com)
    - Auto-detects post types for content categorization
    - Calculates engagement scores and video potential
    - Provides formatted output for AI content analysis
    """

    def __init__(
        self,
        subreddit: str = "SaintMeghanMarkle",
        min_upvotes: int = 200,
        max_posts: int = 20,
        default_subreddit: str = "SaintMeghanMarkle"
    ):
        """
        Initialize Reddit scraper.

        Args:
            subreddit: Subreddit name to scrape (default: "SaintMeghanMarkle")
            min_upvotes: Minimum upvotes threshold (default: 200)
            max_posts: Maximum posts to collect (default: 20)
            default_subreddit: Fallback subreddit if target doesn't exist
        """
        self.subreddit = subreddit
        self.min_upvotes = min_upvotes
        self.max_posts = max_posts
        self.default_subreddit = default_subreddit

        # HTTP headers to appear as regular browser (updated user agent)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        logger.info(
            f"🔴 Initialized Reddit scraper for r/{subreddit} "
            f"(min_upvotes: {min_upvotes})"
        )

    def _detect_post_type(self, title: str, flair: str = "") -> str:
        """
        Auto-detect post type based on title and flair.

        Args:
            title: Post title
            flair: Post flair (if available)

        Returns:
            Post type: "Timeline", "Evidence", "News", "Speculation", or "Discussion"
        """
        title_lower = title.lower()
        flair_lower = flair.lower() if flair else ""

        # Check flair first (more reliable)
        if "timeline" in flair_lower:
            return "Timeline"
        elif "evidence" in flair_lower or "receipts" in flair_lower:
            return "Evidence"
        elif "news" in flair_lower or "breaking" in flair_lower:
            return "News"
        elif "speculation" in flair_lower or "theory" in flair_lower:
            return "Speculation"

        # Check title
        timeline_keywords = ["timeline", "chronology", "sequence", "order of events"]
        evidence_keywords = ["proof", "evidence", "receipts", "facts", "documents"]
        news_keywords = ["breaking", "news", "reports", "announces", "confirmed"]
        speculation_keywords = ["theory", "i think", "might", "possibly", "speculation", "could be"]

        if any(kw in title_lower for kw in timeline_keywords):
            return "Timeline"
        elif any(kw in title_lower for kw in evidence_keywords):
            return "Evidence"
        elif any(kw in title_lower for kw in news_keywords):
            return "News"
        elif any(kw in title_lower for kw in speculation_keywords):
            return "Speculation"
        else:
            return "Discussion"

    def _calculate_video_potential(
        self,
        engagement_score: int,
        post_type: str
    ) -> str:
        """
        Calculate video potential based on engagement and post type.

        Args:
            engagement_score: Calculated engagement score
            post_type: Type of post

        Returns:
            Video potential indicator: "🟢 HIGH", "🟡 MEDIUM", or "🔴 LOW"
        """
        high_value_types = ["Timeline", "Evidence", "News"]

        if engagement_score > 500 and post_type in high_value_types:
            return "🟢 HIGH"
        elif engagement_score >= 300:
            return "🟡 MEDIUM"
        else:
            return "🔴 LOW"

    def _validate_subreddit(self, subreddit: str) -> bool:
        """
        Check if subreddit exists before scraping.

        Args:
            subreddit: Subreddit name to check

        Returns:
            True if exists, False if 404/banned
        """
        try:
            # Check about.json
            url = f"https://www.reddit.com/r/{subreddit}/about.json"
            # Use minimal headers for check to avoid strict blocks on simple JSON check
            headers = {'User-Agent': self.headers['User-Agent']}
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                return True
            elif response.status_code == 404 or response.status_code == 403:  # Not found or private
                return False
                
            # If other error (rate limit, server error), assume valid to be safe/retry later
            return True
            
        except Exception as e:
            logger.debug(f"Subreddit validation error: {e}")
            return True # Fail open on network errors

    @retry(
        wait=wait_fixed(5),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(requests.RequestException)
    )
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch Reddit page with retry logic.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            logger.debug(f"Fetching: {url}")

            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            return soup

        except requests.RequestException as e:
            logger.error(f"❌ Error fetching {url}: {e}")
            raise

    def collect(self, hours_back: int = 24, keywords: List[str] = None) -> Dict:
        """
        Scrape Reddit posts from specified subreddit OR search keywords.

        Args:
            hours_back: Hours to look back (default: 24)
            keywords: List of keywords to search (optional, used if subreddit is None)

        Returns:
            Dictionary containing collected post data
        """
        is_search = False
        target = f"r/{self.subreddit}"
        
        # Determine if we should search instead of scrape subreddit
        if (not self.subreddit or self.subreddit == "SaintMeghanMarkle") and keywords:
             # If default/empty subreddit but we have keywords, use search
             is_search = True
             query = " OR ".join([f'"{k}"' for k in keywords[:3]]) # Limit to 3 keywords to avoid too long query
             target = f"Search: {query}"
             logger.info(f"🔴 Searching Reddit: {query} (past {hours_back}h)")
        else:
            # Validate subreddit existence
            if not self._validate_subreddit(self.subreddit):
                logger.warning(f"⚠️  Subreddit r/{self.subreddit} invalid/404. Falling back to default: r/{self.default_subreddit}")
                self.subreddit = self.default_subreddit
            
            logger.info(f"🔴 Scraping Reddit: r/{self.subreddit} (past {hours_back}h)")

        results = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "subreddit": self.subreddit if not is_search else "Search",
            "total_posts_found": 0,
            "posts": []
        }

        try:
            # Construct URL
            if is_search:
                # search query
                import urllib.parse
                encoded_query = urllib.parse.quote(query)
                # t=day (24h) or t=week depending on hours_back
                time_filter = 'day'
                if hours_back > 24:
                    time_filter = 'week'
                url = f"https://old.reddit.com/search?q={encoded_query}&sort=relevance&t={time_filter}"
            else:
                url = f"https://old.reddit.com/r/{self.subreddit}/hot/"
            
            soup = self._fetch_page(url)

            if not soup:
                logger.warning(f"⚠️  Failed to fetch r/{self.subreddit}")
                return results

            # Calculate cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

            # Find all post containers
            posts = soup.find_all('div', {'class': 'thing', 'data-type': 'link'})

            logger.debug(f"Found {len(posts)} posts on page")

            processed_posts = []

            for post in posts:
                try:
                    # Extract post ID
                    post_id = post.get('data-fullname', '').replace('t3_', '')
                    if not post_id:
                        continue

                    # Extract upvotes
                    upvotes_elem = post.find('div', class_='score unvoted')
                    if not upvotes_elem:
                        upvotes_elem = post.find('div', class_='score likes')
                    if not upvotes_elem:
                        upvotes_elem = post.find('div', class_='score dislikes')

                    upvotes_text = upvotes_elem.get_text(strip=True) if upvotes_elem else "0"

                    # Parse upvotes (handle "k" notation)
                    try:
                        if 'k' in upvotes_text.lower():
                            upvotes = int(float(upvotes_text.lower().replace('k', '')) * 1000)
                        else:
                            upvotes = int(upvotes_text)
                    except (ValueError, AttributeError):
                        upvotes = 0

                    # Filter by minimum upvotes
                    if upvotes < self.min_upvotes:
                        continue

                    # Extract title
                    title_elem = post.find('a', class_='title')
                    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

                    # Extract author
                    author_elem = post.find('a', class_='author')
                    author = author_elem.get_text(strip=True) if author_elem else "[deleted]"

                    # Extract timestamp
                    time_elem = post.find('time')
                    if time_elem and time_elem.get('datetime'):
                        created_utc = datetime.fromisoformat(
                            time_elem['datetime'].replace('Z', '+00:00')
                        )
                    else:
                        # Fallback: try data-timestamp attribute
                        timestamp_attr = post.get('data-timestamp')
                        if timestamp_attr:
                            created_utc = datetime.fromtimestamp(
                                int(timestamp_attr) / 1000,
                                tz=timezone.utc
                            )
                        else:
                            created_utc = datetime.now(timezone.utc)

                    # Check if post is within time window
                    if created_utc < cutoff_time:
                        continue

                    # Calculate hours ago
                    hours_ago = (
                        datetime.now(timezone.utc) - created_utc
                    ).total_seconds() / 3600

                    # Extract comment count
                    comments_elem = post.find('a', class_='comments')
                    comments_text = comments_elem.get_text(strip=True) if comments_elem else "0"
                    try:
                        num_comments = int(re.search(r'\d+', comments_text).group())
                    except (AttributeError, ValueError):
                        num_comments = 0

                    # Extract upvote ratio (if available)
                    upvote_ratio = 1.0  # Default
                    ratio_elem = post.find('span', class_='number')
                    if ratio_elem:
                        ratio_text = ratio_elem.get_text(strip=True)
                        try:
                            upvote_ratio = float(ratio_text.rstrip('%')) / 100
                        except (ValueError, AttributeError):
                            pass

                    # Extract flair
                    flair_elem = post.find('span', class_='linkflairlabel')
                    flair = flair_elem.get_text(strip=True) if flair_elem else "General"

                    # Extract post URL
                    post_url = f"https://reddit.com{post.get('data-permalink', '')}"

                    # Extract selftext (for text posts)
                    selftext = ""
                    expando = post.find('div', class_='expando')
                    if expando:
                        usertext = expando.find('div', class_='md')
                        if usertext:
                            selftext = usertext.get_text(strip=True)[:500]

                    # Extract link URL (for link posts)
                    link_url = None
                    link_elem = post.find('a', class_='thumbnail')
                    if link_elem and link_elem.get('href'):
                        href = link_elem['href']
                        if not href.startswith('/r/'):
                            link_url = href

                    # Detect post type
                    post_type = self._detect_post_type(title, flair)

                    # Calculate engagement score
                    engagement_score = upvotes + (num_comments * 2)

                    # Calculate video potential
                    video_potential = self._calculate_video_potential(
                        engagement_score,
                        post_type
                    )

                    # Build post data
                    post_data = {
                        "post_id": post_id,
                        "title": title,
                        "author": author,
                        "upvotes": upvotes,
                        "upvote_ratio": round(upvote_ratio, 2),
                        "num_comments": num_comments,
                        "created_utc": created_utc.isoformat(),
                        "url": post_url,
                        "post_type": post_type,
                        "selftext": selftext,
                        "link_url": link_url,
                        "flair": flair,
                        "top_comment": "",  # Would need separate request
                        "top_comment_upvotes": 0,
                        "hours_ago": round(hours_ago, 1),
                        "engagement_score": engagement_score,
                        "video_potential": video_potential
                    }

                    processed_posts.append(post_data)

                    # Stop if we have enough posts
                    if len(processed_posts) >= self.max_posts:
                        break

                except Exception as e:
                    logger.warning(f"⚠️  Error processing post: {e}")
                    continue

            # Sort by engagement score
            processed_posts.sort(key=lambda x: x['engagement_score'], reverse=True)

            results["posts"] = processed_posts
            results["total_posts_found"] = len(processed_posts)

            # Log post type breakdown
            type_counts = {}
            for post in processed_posts:
                ptype = post['post_type']
                type_counts[ptype] = type_counts.get(ptype, 0) + 1

            type_summary = ", ".join([f"{k}={v}" for k, v in type_counts.items()])
            logger.info(
                f"✅ Found {len(processed_posts)} posts meeting criteria "
                f"(min {self.min_upvotes} upvotes)"
            )
            logger.info(f"Post types: {type_summary}")

            # Rate limiting delay
            time.sleep(2)

        except Exception as e:
            logger.error(f"❌ Reddit scraping error: {e}")
            results["error"] = str(e)

        return results

    def format_for_prompt(self, data: Dict) -> str:
        """
        Format collected Reddit data for AI prompt injection.

        Args:
            data: Dictionary returned from collect() method

        Returns:
            Formatted string with clear sections and visual separators
        """
        output = []

        # Header
        output.append("═" * 70)
        output.append("🔴 REDDIT COMMUNITY ANALYSIS")
        output.append("═" * 70)
        output.append(f"Collected: {data.get('timestamp', 'N/A')}")
        output.append(f"Subreddit: r/{data.get('subreddit', 'Unknown')}")
        output.append(f"Total Posts Found: {data.get('total_posts_found', 0)}")
        output.append("")

        # Check for errors
        if "error" in data:
            output.append(f"❌ ERROR: {data['error']}")
            return "\n".join(output)

        posts = data.get("posts", [])

        if not posts:
            output.append("ℹ️  No posts found meeting criteria")
            output.append("")
            return "\n".join(output)

        # Group posts by type
        posts_by_type = {}
        for post in posts:
            ptype = post.get('post_type', 'Discussion')
            if ptype not in posts_by_type:
                posts_by_type[ptype] = []
            posts_by_type[ptype].append(post)

        # Display posts grouped by type
        for post_type in ["Timeline", "Evidence", "News", "Speculation", "Discussion"]:
            if post_type not in posts_by_type:
                continue

            type_posts = posts_by_type[post_type]

            output.append("─" * 70)
            output.append(f"📁 {post_type.upper()} ({len(type_posts)} posts)")
            output.append("─" * 70)
            output.append("")

            for post in type_posts[:5]:  # Top 5 per type
                output.append(f"{post['video_potential']}")
                output.append(f"Title: {post['title']}")
                output.append("")

                output.append(f"📊 Engagement:")
                output.append(f"   ⬆️  Upvotes: {post['upvotes']:,}")
                output.append(f"   💬 Comments: {post['num_comments']:,}")
                output.append(f"   📈 Upvote Ratio: {int(post['upvote_ratio'] * 100)}%")
                output.append(f"   🎯 Engagement Score: {post['engagement_score']:,}")
                output.append("")

                output.append(f"👤 Author: u/{post['author']}")
                output.append(f"🏷️  Flair: {post['flair']}")
                output.append(f"⏰ Posted: {post['hours_ago']}h ago")
                output.append("")

                if post['selftext']:
                    output.append(f"📝 Excerpt:")
                    output.append(f"   {post['selftext'][:200]}...")
                    output.append("")

                output.append(f"🔗 URL: {post['url']}")
                output.append("")

                # Suggested video angle
                if post['video_potential'] == "🟢 HIGH":
                    output.append("💡 SUGGESTED ANGLE: Deep-dive analysis video")
                elif post['video_potential'] == "🟡 MEDIUM":
                    output.append("💡 SUGGESTED ANGLE: Commentary/discussion video")
                else:
                    output.append("💡 SUGGESTED ANGLE: Community roundup mention")
                output.append("")

                output.append("─" * 70)
                output.append("")

        # Summary section
        output.append("═" * 70)
        output.append("🎯 VIDEO OPPORTUNITY SUMMARY")
        output.append("═" * 70)
        output.append("")

        # Top 3 by engagement
        output.append("🏆 TOP 3 BY ENGAGEMENT:")
        for i, post in enumerate(posts[:3], 1):
            output.append(
                f"   {i}. [{post['post_type']}] {post['engagement_score']:,} engagement"
            )
            output.append(f"      \"{post['title'][:60]}...\"")
            output.append(f"      {post['url']}")
            output.append("")

        # Trending themes
        output.append("🔥 TRENDING THEMES:")
        type_counts = {}
        for post in posts:
            ptype = post['post_type']
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

        for ptype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            output.append(f"   • {ptype}: {count} posts")
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
    Test the Reddit scraper with real scraping.
    """
    import config
    from utils.settings_manager import KeywordManager

    print("=" * 70)
    print("🔴 TESTING REDDIT SCRAPER")
    print("=" * 70)
    print()

    # Load keywords for filtering
    kw_mgr = KeywordManager()
    active_keywords = kw_mgr.get_active()
    
    print(f"🔑 Tracking keywords: {', '.join(active_keywords)}")
    
    # Initialize scraper
    scraper = RedditScraper(
        subreddit="SaintMeghanMarkle",
        min_upvotes=100,  # Lower threshold for testing
        max_posts=10
    )

    print("🔍 Scraping r/SaintMeghanMarkle...")
    print("(This may take a few seconds)")
    print()

    try:
        # Collect data
        data = scraper.collect(hours_back=48)  # 48h for more results

        # Show summary
        print()
        print("=" * 70)
        print("📊 RAW DATA SUMMARY")
        print("=" * 70)
        print(f"Total posts found: {data['total_posts_found']}")
        print(f"Subreddit: {data['subreddit']}")
        print(f"Collection time: {data['timestamp']}")
        print()

        if data['posts']:
            print("First post sample:")
            post = data['posts'][0]
            print(f"  Title: {post['title']}")
            print(f"  Type: {post['post_type']}")
            print(f"  Upvotes: {post['upvotes']}")
            print(f"  Comments: {post['num_comments']}")
            print(f"  Video Potential: {post['video_potential']}")
            print()

        # Show formatted output
        print("=" * 70)
        print("📝 FORMATTED OUTPUT (For AI Prompts)")
        print("=" * 70)
        print()
        formatted = scraper.format_for_prompt(data)
        print(formatted)

        print()
        print("=" * 70)
        print("✅ REDDIT SCRAPER TEST COMPLETE")
        print("=" * 70)
        print()
        print("USAGE IN YOUR APPLICATION:")
        print()
        print("from collectors.reddit_scraper import RedditScraper")
        print()
        print("scraper = RedditScraper(")
        print("    subreddit='SaintMeghanMarkle',")
        print("    min_upvotes=200,")
        print("    max_posts=20")
        print(")")
        print("data = scraper.collect(hours_back=24)")
        print("formatted_text = scraper.format_for_prompt(data)")
        print()

    except Exception as e:
        print()
        print(f"❌ ERROR during scraping: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
