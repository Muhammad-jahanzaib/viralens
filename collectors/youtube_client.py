"""
YouTube Competitor Tracker

This module tracks competitor YouTube channels to analyze their video titles,
thumbnails, view counts, and performance patterns for competitive intelligence.

Features:
- Tracks latest videos from competitor channels
- Calculates views per hour and engagement metrics
- Analyzes title patterns and keywords
- Provides formatted competitive intelligence reports
- Uses regex for pattern matching
"""

import os
import sys
import re
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from collections import Counter

import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.rate_limiter import YOUTUBE_LIMITER


class YouTubeCompetitorTracker:
    """
    Tracks and analyzes competitor YouTube channels for competitive intelligence.

    Features:
    - Monitors latest videos from competitor channels
    - Calculates performance metrics (VPH, engagement rate)
    - Analyzes title patterns and keywords
    - Provides formatted competitive intelligence
    - Quota-aware collection with automatic adjustment
    """

    # YouTube API quota costs
    SEARCH_COST = 100  # Each search() costs 100 units
    VIDEO_DETAILS_COST = 1  # Each videos().list() costs 1 unit
    DAILY_QUOTA_LIMIT = 10000  # YouTube API daily quota limit

    def __init__(
        self,
        api_key: str,
        competitor_channels: Dict[str, str] = None
    ):
        """
        Initialize YouTube competitor tracker.

        Args:
            api_key: YouTube Data API v3 key
            competitor_channels: Dict mapping channel names to channel IDs
                Example: {"Jessica Talks Tea": "UCxxxxxxx"}

        Example:
            >>> tracker = YouTubeCompetitorTracker(
            ...     api_key="YOUR_API_KEY",
            ...     competitor_channels={"Channel Name": "UC..."}
            ... )
        """
        # Validate API key
        if not api_key:
            raise ValueError("API Key is required")

        self.api_key = api_key
        self.quota_used = 0
        self.title_patterns = []
        self.quota_file = 'data/youtube_quota.json'
        self.quota_used_today = self._load_quota_usage()

        # Load from settings if not provided
        if competitor_channels is None:
            from utils.settings_manager import CompetitorManager
            comp_mgr = CompetitorManager()
            active_comps = comp_mgr.get_active()
            self.competitor_channels = {c['name']: c['channel_id'] for c in active_comps}
            logger.info(f"📺 Loaded {len(self.competitor_channels)} competitors from settings")
        else:
            self.competitor_channels = competitor_channels

        # Initialize YouTube API client
        try:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            remaining_quota = self.DAILY_QUOTA_LIMIT - self.quota_used_today
            logger.info(
                f"📺 Initialized YouTube tracker for {len(self.competitor_channels)} channels "
                f"(Quota: {self.quota_used_today}/{self.DAILY_QUOTA_LIMIT} used, {remaining_quota} remaining)"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize YouTube client: {e}")
            raise

    def _calculate_performance_rating(self, vph: float) -> str:
        """
        Calculate performance rating based on views per hour.

        Args:
            vph: Views per hour

        Returns:
            Performance rating string
        """
        if vph > 5000:
            return "🔥 VIRAL"
        elif vph >= 1000:
            return "🚀 GOOD"
        elif vph >= 500:
            return "✅ AVERAGE"
        else:
            return "💤 FLOPPED"

    def _load_quota_usage(self) -> int:
        """Load today's quota usage from file"""

        if not os.path.exists(self.quota_file):
            return 0

        try:
            with open(self.quota_file, 'r') as f:
                data = json.load(f)

            # Check if it's today's data
            last_date = data.get('date')
            today = datetime.utcnow().strftime('%Y-%m-%d')

            if last_date == today:
                usage = data.get('quota_used', 0)
                logger.debug(f"📊 Loaded quota usage: {usage}/10000")
                return usage
            else:
                # New day, reset
                logger.info(f"🔄 New day detected, resetting quota counter")
                return 0
        except Exception as e:
            logger.warning(f"⚠️  Error loading quota file: {e}")
            return 0

    def _save_quota_usage(self, additional_cost: int):
        """Save updated quota usage"""

        self.quota_used_today += additional_cost
        self.quota_used += additional_cost  # Keep existing tracking

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)

        try:
            with open(self.quota_file, 'w') as f:
                json.dump({
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'quota_used': self.quota_used_today
                }, f, indent=2)

            logger.debug(f"💾 Saved quota usage: {self.quota_used_today}/10000")
        except Exception as e:
            logger.warning(f"⚠️  Error saving quota file: {e}")

    @retry(
        wait=wait_fixed(3),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(Exception)
    )
    def _search_channel_videos(
        self,
        channel_id: str,
        max_results: int,
        published_after: Optional[datetime] = None
    ) -> List[str]:
        """
        Search for recent videos from a channel.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum videos to return
            published_after: Only return videos after this time

        Returns:
            List of video IDs
        """
        try:
            params = {
                'part': 'id',
                'channelId': channel_id,
                'order': 'date',
                'type': 'video',
                'maxResults': max_results
            }

            if published_after:
                params['publishedAfter'] = published_after.isoformat()

            response = self.youtube.search().list(**params).execute()

            self.quota_used += 100  # search().list() costs 100 units

            video_ids = []
            for item in response.get('items', []):
                id_data = item.get('id', {})
                if isinstance(id_data, dict) and 'videoId' in id_data:
                    video_ids.append(id_data['videoId'])

            return video_ids

        except HttpError as e:
            logger.error(f"❌ YouTube API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error searching videos: {e}")
            raise

    @retry(
        wait=wait_fixed(3),
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type(Exception)
    )
    def _get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Get detailed information for videos.

        Args:
            video_ids: List of video IDs

        Returns:
            List of video detail dictionaries
        """
        if not video_ids:
            return []

        try:
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()

            self.quota_used += 1  # videos().list() costs 1 unit

            return response.get('items', [])

        except HttpError as e:
            logger.error(f"❌ YouTube API error getting video details: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error getting video details: {e}")
            raise

    def collect(
        self,
        hours_back: int = 48,
        videos_per_channel: int = 5
    ) -> Dict:
        """
        Collect latest videos from all competitor channels.

        Args:
            hours_back: Hours to look back for videos (default: 48)
            videos_per_channel: Max videos to fetch per channel (default: 5)

        Returns:
            Dictionary containing competitor video data with structure:
            {
                "timestamp": "2026-01-18 16:30:00 UTC",
                "monitoring_window": "48 hours",
                "total_videos_found": 15,
                "channels_monitored": 3,
                "competitor_data": [...]
            }

        Example:
            >>> data = tracker.collect(hours_back=48, videos_per_channel=5)
        """
        channel_names = list(self.competitor_channels.keys())
        logger.info(f"📺 Tracking YouTube competitors: {', '.join(channel_names)}")

        # Estimate quota cost
        num_channels = len(self.competitor_channels)
        estimated_cost = num_channels * (self.SEARCH_COST + videos_per_channel * self.VIDEO_DETAILS_COST)
        remaining_quota = self.DAILY_QUOTA_LIMIT - self.quota_used_today

        logger.info(f"📊 Estimated quota cost: {estimated_cost} (Remaining: {remaining_quota}/{self.DAILY_QUOTA_LIMIT})")

        # Check if we have enough quota
        if estimated_cost > remaining_quota:
            logger.warning(f"⚠️  Estimated cost ({estimated_cost}) exceeds remaining quota ({remaining_quota})")

            # Try to adjust number of channels
            if remaining_quota > 0:
                max_channels = int(remaining_quota / (self.SEARCH_COST + videos_per_channel * self.VIDEO_DETAILS_COST))
                if max_channels > 0:
                    logger.info(f"📉 Reducing from {num_channels} to {max_channels} channels to stay within quota")
                    # Keep only first N channels
                    self.competitor_channels = dict(list(self.competitor_channels.items())[:max_channels])
                    channel_names = list(self.competitor_channels.keys())
                else:
                    logger.error(f"❌ No quota remaining for YouTube collection today")
                    return {
                        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "monitoring_window": f"{hours_back} hours",
                        "total_videos_found": 0,
                        "channels_monitored": 0,
                        "competitor_data": [],
                        "quota_exceeded": True,
                        "quota_used": 0
                    }
            else:
                return {
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "monitoring_window": f"{hours_back} hours",
                    "total_videos_found": 0,
                    "channels_monitored": 0,
                    "competitor_data": [],
                    "quota_exceeded": True,
                    "quota_used": 0
                }

        results = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "monitoring_window": f"{hours_back} hours",
            "total_videos_found": 0,
            "channels_monitored": len(self.competitor_channels),
            "competitor_data": [],
            "quota_used": 0,
            "quota_exceeded": False
        }

        # Calculate cutoff time
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        for channel_name, channel_id in self.competitor_channels.items():
            try:
                logger.info(f"Fetching latest videos from {channel_name}...")

                # Search for recent videos
                video_ids = self._search_channel_videos(
                    channel_id,
                    videos_per_channel * 2,  # Get more, filter later
                    published_after=cutoff_time
                )
                results["quota_used"] += self.SEARCH_COST  # Track search cost

                # If no recent videos, get latest regardless of date
                if not video_ids:
                    logger.info(
                        f"ℹ️  No videos from {channel_name} in past {hours_back}h, "
                        f"fetching latest videos..."
                    )
                    video_ids = self._search_channel_videos(
                        channel_id,
                        videos_per_channel,
                        published_after=None
                    )
                    results["quota_used"] += self.SEARCH_COST  # Track second search

                if not video_ids:
                    logger.warning(f"⚠️  No videos found for {channel_name}")
                    results["competitor_data"].append({
                        "channel_name": channel_name,
                        "channel_id": channel_id,
                        "videos": [],
                        "channel_insights": {}
                    })
                    continue

                # Get video details
                video_details = self._get_video_details(video_ids[:videos_per_channel])
                results["quota_used"] += len(video_ids[:videos_per_channel]) * self.VIDEO_DETAILS_COST  # Track video details cost

                # Process videos
                processed_videos = []
                total_views = 0
                total_duration = 0
                best_vph = 0
                best_video_id = None

                for video in video_details:
                    try:
                        snippet = video.get('snippet', {})
                        statistics = video.get('statistics', {})
                        content_details = video.get('contentDetails', {})

                        # Extract data
                        video_id = video['id']
                        title = snippet.get('title', 'Untitled')
                        description = snippet.get('description', '')[:200]
                        published_at_str = snippet.get('publishedAt', '')

                        # Parse published time
                        published_at = datetime.fromisoformat(
                            published_at_str.replace('Z', '+00:00')
                        )

                        # Get statistics (may be disabled for some videos)
                        view_count = int(statistics.get('viewCount', 0))
                        like_count = int(statistics.get('likeCount', 0))
                        comment_count = int(statistics.get('commentCount', 0))

                        # Parse duration
                        duration_str = content_details.get('duration', 'PT0S')
                        try:
                            duration_seconds = isodate.parse_duration(duration_str).total_seconds()
                            duration_minutes = duration_seconds / 60
                        except Exception:
                            duration_minutes = 0

                        # Calculate hours since upload
                        hours_since_upload = (
                            datetime.now(timezone.utc) - published_at
                        ).total_seconds() / 3600

                        # Calculate VPH (avoid division by zero)
                        if hours_since_upload >= 0.1:
                            views_per_hour = view_count / hours_since_upload
                        else:
                            views_per_hour = 0

                        # Calculate engagement rate
                        if view_count > 0:
                            engagement_rate = ((like_count + comment_count) / view_count) * 100
                        else:
                            engagement_rate = 0

                        # Get thumbnail URL (prefer maxresdefault)
                        thumbnails = snippet.get('thumbnails', {})
                        if 'maxresdefault' in thumbnails:
                            thumbnail_url = thumbnails['maxresdefault']['url']
                        elif 'standard' in thumbnails:
                            thumbnail_url = thumbnails['standard']['url']
                        elif 'high' in thumbnails:
                            thumbnail_url = thumbnails['high']['url']
                        else:
                            thumbnail_url = thumbnails.get('default', {}).get('url', '')

                        # Build video data
                        video_data = {
                            "video_id": video_id,
                            "title": title,
                            "description": description,
                            "channel_name": channel_name,
                            "channel_id": channel_id,
                            "published_at": published_at.isoformat(),
                            "view_count": view_count,
                            "like_count": like_count,
                            "comment_count": comment_count,
                            "duration": duration_str,
                            "duration_minutes": round(duration_minutes, 2),
                            "thumbnail_url": thumbnail_url,
                            "video_url": f"https://youtube.com/watch?v={video_id}",
                            "hours_since_upload": round(hours_since_upload, 1),
                            "views_per_hour": round(views_per_hour, 2),
                            "engagement_rate": round(engagement_rate, 2),
                            "performance_rating": self._calculate_performance_rating(views_per_hour)
                        }

                        processed_videos.append(video_data)

                        # Track for insights
                        total_views += view_count
                        total_duration += duration_minutes

                        if views_per_hour > best_vph:
                            best_vph = views_per_hour
                            best_video_id = video_id

                    except Exception as e:
                        logger.warning(f"⚠️  Error processing video {video.get('id')}: {e}")
                        continue

                # Calculate channel insights
                channel_insights = {}
                if processed_videos:
                    channel_insights = {
                        "avg_views_per_hour": round(
                            sum(v['views_per_hour'] for v in processed_videos) / len(processed_videos),
                            2
                        ),
                        "avg_duration_minutes": round(total_duration / len(processed_videos), 2),
                        "total_views": total_views,
                        "best_performing_video": best_video_id
                    }

                    logger.info(
                        f"✅ Found {len(processed_videos)} videos from {channel_name} "
                        f"(past {hours_back}h)"
                    )

                    # Log best performer
                    if best_video_id:
                        best_video = next(v for v in processed_videos if v['video_id'] == best_video_id)
                        logger.info(
                            f"Best performer: '{best_video['title']}' - "
                            f"{best_vph:.1f} VPH"
                        )

                results["competitor_data"].append({
                    "channel_name": channel_name,
                    "channel_id": channel_id,
                    "videos": processed_videos,
                    "channel_insights": channel_insights
                })

                results["total_videos_found"] += len(processed_videos)

            except Exception as e:
                logger.error(f"❌ Error collecting videos for {channel_name}: {e}")
                results["competitor_data"].append({
                    "channel_name": channel_name,
                    "channel_id": channel_id,
                    "videos": [],
                    "channel_insights": {},
                    "error": str(e)
                })
                continue

        # Log quota usage
        remaining = 10000 - self.quota_used
        logger.info(
            f"API Quota used: {self.quota_used} units (~{remaining} remaining today)"
        )

        if self.quota_used > 9000:
            logger.warning("⚠️  Approaching daily API quota limit!")

        # Save quota usage
        self._save_quota_usage(results["quota_used"])

        logger.info(
            f"✅ YouTube tracking complete: {results['total_videos_found']} videos "
            f"from {results['channels_monitored']} channels, {results['quota_used']} quota used"
        )

        # Analyze title patterns
        all_videos = []
        for channel_data in results["competitor_data"]:
            all_videos.extend(channel_data.get('videos', []))

        # Add advanced title analysis
        if all_videos:
            title_patterns = self._analyze_title_patterns(all_videos)
            results['viral_patterns'] = title_patterns
        else:
            results['viral_patterns'] = {}

        return results

    def _analyze_title_patterns(self, videos: List[Dict]) -> Dict:
        """
        Analyze patterns in competitor titles
        
        Returns:
            Dict with pattern analysis
        """
        
        patterns = {
            'structure_patterns': self._extract_structure_patterns(videos),
            'word_patterns': self._extract_word_patterns(videos),
            'viral_formulas': self._extract_viral_formulas(videos),
            'performance_analysis': self._analyze_performance_by_pattern(videos)
        }
        
        return patterns
    
    def _extract_structure_patterns(self, videos: List[Dict]) -> List[Dict]:
        """Extract title structure patterns"""
        
        structures = []
        
        for video in videos:
            title = video.get('title', '')
            
            # Analyze structure
            structure = {
                'title': title,
                'length': len(title),
                'has_colon': ':' in title,
                'has_hyphen': ' - ' in title,
                'has_pipe': '|' in title,
                'has_question': '?' in title,
                'has_exclamation': '!' in title,
                'has_quotes': '"' in title or "'" in title,
                'has_parentheses': '(' in title,
                'has_emoji': any(ord(c) > 127 for c in title),
                'caps_words': len(re.findall(r'\b[A-Z]{2,}\b', title)),
                'number_words': len(re.findall(r'\b\d+\b', title)),
                'vph': video.get('views_per_hour', 0)  # Performance metric
            }
            
            structures.append(structure)
        
        return structures
    
    def _extract_word_patterns(self, videos: List[Dict]) -> Dict:
        """Extract common word patterns and phrases"""
        
        # Collect all words
        all_words = []
        all_bigrams = []
        all_trigrams = []
        
        for video in videos:
            title = video.get('title', '').upper()
            words = re.findall(r'\b[A-Z]{2,}\b', title)  # CAPS words only
            
            all_words.extend(words)
            
            # Extract phrases (2-3 word combinations)
            title_words = title.split()
            for i in range(len(title_words) - 1):
                all_bigrams.append(' '.join(title_words[i:i+2]))
            for i in range(len(title_words) - 2):
                all_trigrams.append(' '.join(title_words[i:i+3]))
        
        # Count frequencies
        word_freq = Counter(all_words)
        bigram_freq = Counter(all_bigrams)
        trigram_freq = Counter(all_trigrams)
        
        return {
            'top_power_words': word_freq.most_common(20),
            'top_phrases_2word': bigram_freq.most_common(15),
            'top_phrases_3word': trigram_freq.most_common(10)
        }
    
    def _extract_viral_formulas(self, videos: List[Dict]) -> List[Dict]:
        """
        Identify specific title formulas that went viral
        
        Returns:
            List of viral title formulas with examples
        """
        
        # Sort by performance
        sorted_videos = sorted(videos, key=lambda v: v.get('views_per_hour', 0), reverse=True)
        
        # Take top 30% as "viral"
        viral_threshold = int(len(sorted_videos) * 0.3)
        viral_videos = sorted_videos[:max(viral_threshold, 5)]
        
        formulas = []
        
        for video in viral_videos:
            title = video.get('title', '')
            
            # Extract formula by replacing specific names/topics with placeholders
            formula = self._generalize_title(title)
            
            formulas.append({
                'original_title': title,
                'formula': formula,
                'vph': video.get('views_per_hour', 0),
                'views': video.get('view_count', 0),
                'published': video.get('hours_since_upload', 0),
                'channel': video.get('channel_name', ''),
                'pattern_type': self._classify_pattern(title)
            })
        
        return formulas
    
    def _generalize_title(self, title: str) -> str:
        """
        Convert specific title to generalized formula
        
        Example:
        "Meghan Markle EXPOSED: Netflix Deal FALLS APART"
        → "{PERSON} EXPOSED: {TOPIC} FALLS APART"
        """
        
        formula = title
        
        # Replace common names with placeholders
        names = ['Meghan', 'Markle', 'Harry', 'Kate', 'William', 'Charles', 
                'Diana', 'Queen', 'King', 'Prince', 'Princess']
        
        for name in names:
            formula = re.sub(rf'\b{name}\b', '{PERSON}', formula, flags=re.IGNORECASE)
        
        # Replace common topics
        topics = ['Netflix', 'Royal', 'Palace', 'Family', 'Wedding', 'Interview',
                 'Lawsuit', 'Deal', 'Protocol', 'Scandal']
        
        for topic in topics:
            formula = re.sub(rf'\b{topic}\b', '{TOPIC}', formula, flags=re.IGNORECASE)
        
        # Collapse repeated placeholders
        formula = re.sub(r'(\{PERSON\}\s*)+', '{PERSON} ', formula)
        formula = re.sub(r'(\{TOPIC\}\s*)+', '{TOPIC} ', formula)
        formula = re.sub(r'\s+', ' ', formula).strip()

        # Identify structure markers
        if ':' in formula:
            parts = formula.split(':')
            if len(parts) == 2:
                formula = f"{parts[0].strip()}: {{CONSEQUENCE}}"
        
        return formula
    
    def _classify_pattern(self, title: str) -> str:
        """Classify the title pattern type"""
        
        title_upper = title.upper()
        
        if 'EXPOSED' in title_upper or 'REVEALS' in title_upper:
            return 'REVELATION'
        elif 'BREAKING' in title_upper or 'JUST IN' in title_upper:
            return 'BREAKING_NEWS'
        elif '?' in title:
            return 'QUESTION'
        elif 'VS' in title_upper or 'V.' in title_upper:
            return 'COMPARISON'
        elif any(word in title_upper for word in ['TRUTH', 'REAL', 'REALLY']):
            return 'TRUTH_SEEKING'
        elif any(word in title_upper for word in ['ANALYZE', 'BREAKDOWN', 'EXPLAINED']):
            return 'ANALYSIS'
        elif re.search(r'\b\d+\b', title):
            return 'NUMBERED_LIST'
        else:
            return 'OTHER'
    
    def _analyze_performance_by_pattern(self, videos: List[Dict]) -> Dict:
        """Analyze which patterns perform best"""
        
        pattern_performance = {}
        
        for video in videos:
            title = video.get('title', '')
            pattern = self._classify_pattern(title)
            vph = video.get('views_per_hour', 0)
            
            if pattern not in pattern_performance:
                pattern_performance[pattern] = {
                    'count': 0,
                    'total_vph': 0,
                    'examples': []
                }
            
            pattern_performance[pattern]['count'] += 1
            pattern_performance[pattern]['total_vph'] += vph
            
            if len(pattern_performance[pattern]['examples']) < 3:
                pattern_performance[pattern]['examples'].append({
                    'title': title,
                    'vph': vph,
                    'channel': video.get('channel_name', '')
                })
        
        # Calculate averages
        for pattern in pattern_performance:
            count = pattern_performance[pattern]['count']
            pattern_performance[pattern]['avg_vph'] = (
                pattern_performance[pattern]['total_vph'] / count if count > 0 else 0
            )
        
        # Sort by performance
        sorted_patterns = sorted(
            pattern_performance.items(),
            key=lambda x: x[1]['avg_vph'],
            reverse=True
        )
        
        return {
            'by_pattern': dict(sorted_patterns),
            'best_performing': sorted_patterns[0][0] if sorted_patterns else None,
            'worst_performing': sorted_patterns[-1][0] if sorted_patterns else None
        }

    def analyze_titles(self, data: Dict) -> Dict:
        """
        Analyze title patterns across all competitor videos.

        Args:
            data: Dictionary returned from collect() method

        Returns:
            Dictionary containing title analysis:
            {
                "common_keywords": [...],
                "name_mentions": {...},
                "emotional_triggers": {...},
                "avg_title_length": float,
                "all_caps_words_avg": float
            }
        """
        all_titles = []

        for channel_data in data.get("competitor_data", []):
            for video in channel_data.get("videos", []):
                all_titles.append(video.get("title", ""))

        if not all_titles:
            return {
                "common_keywords": [],
                "name_mentions": {},
                "emotional_triggers": {},
                "avg_title_length": 0,
                "all_caps_words_avg": 0
            }

        # Extract all words
        all_words = []
        all_caps_count = 0

        for title in all_titles:
            words = title.split()
            all_words.extend(words)

            # Count all-caps words
            caps_words = [w for w in words if w.isupper() and len(w) > 1]
            all_caps_count += len(caps_words)

        # Common keywords (frequent words)
        word_counts = Counter(w.upper() for w in all_words if len(w) > 3)
        common_keywords = word_counts.most_common(10)

        # Name mentions
        names = ["Meghan", "Harry", "Kate", "William", "Charles", "Camilla", "Diana"]
        name_mentions = {}
        for name in names:
            count = sum(1 for title in all_titles if name.lower() in title.lower())
            if count > 0:
                name_mentions[name] = count

        # Emotional triggers
        triggers = {
            "SHOCKING": 0, "BREAKING": 0, "EXPOSED": 0, "REVEALED": 0,
            "CRISIS": 0, "FURIOUS": 0, "TRUTH": 0, "BOMBSHELL": 0,
            "SCANDAL": 0, "DISASTER": 0
        }

        for title in all_titles:
            title_upper = title.upper()
            for trigger in triggers.keys():
                if trigger in title_upper:
                    triggers[trigger] += 1

        emotional_triggers = {k: v for k, v in triggers.items() if v > 0}

        # Average title length
        avg_title_length = sum(len(t) for t in all_titles) / len(all_titles)

        # Average all-caps words per title
        all_caps_words_avg = all_caps_count / len(all_titles) if all_titles else 0

        return {
            "common_keywords": common_keywords,
            "name_mentions": name_mentions,
            "emotional_triggers": emotional_triggers,
            "avg_title_length": round(avg_title_length, 1),
            "all_caps_words_avg": round(all_caps_words_avg, 2)
        }

    def format_for_prompt(self, data: Dict) -> str:
        """
        Format competitor data for AI prompt injection.

        Args:
            data: Dictionary returned from collect() method

        Returns:
            Formatted string with clear sections and visual separators
        """
        output = []

        # Header
        output.append("═" * 70)
        output.append("📺 YOUTUBE COMPETITOR ANALYSIS")
        output.append("═" * 70)
        output.append(f"Collected: {data.get('timestamp', 'N/A')}")
        output.append(f"Monitoring Window: {data.get('monitoring_window', 'N/A')}")
        output.append(f"Channels Tracked: {data.get('channels_monitored', 0)}")
        output.append(f"Total Videos Found: {data.get('total_videos_found', 0)}")
        output.append("")

        # Process each channel
        for channel_data in data.get("competitor_data", []):
            channel_name = channel_data.get("channel_name", "Unknown")
            videos = channel_data.get("videos", [])
            insights = channel_data.get("channel_insights", {})
            error = channel_data.get("error")

            output.append("─" * 70)
            output.append(f"🎬 CHANNEL: {channel_name}")
            output.append(f"Videos Found: {len(videos)}")
            output.append("─" * 70)
            output.append("")

            if error:
                output.append(f"❌ ERROR: {error}")
                output.append("")
                continue

            if not videos:
                output.append("ℹ️  No videos found in monitoring window")
                output.append("")
                continue

            # Display videos
            for video in videos:
                output.append(f"{video['performance_rating']}")
                output.append(f"Title: {video['title']}")
                output.append("")

                output.append(f"📊 Performance:")
                output.append(f"   Views: {video['view_count']:,}")
                output.append(f"   VPH (Views/Hour): {video['views_per_hour']:.1f}")
                output.append(f"   Engagement Rate: {video['engagement_rate']:.2f}%")
                output.append(f"   Duration: {video['duration_minutes']:.1f} min")
                output.append("")

                output.append(f"⏰ Uploaded: {video['hours_since_upload']:.1f}h ago")
                output.append(f"👍 Likes: {video['like_count']:,}")
                output.append(f"💬 Comments: {video['comment_count']:,}")
                output.append("")

                output.append(f"🔗 URL: {video['video_url']}")
                output.append(f"🖼️  Thumbnail: {video['thumbnail_url']}")
                output.append("")

                # Key takeaways
                if video['views_per_hour'] > 3000:
                    output.append("💡 KEY TAKEAWAY: Viral performance - analyze title structure")
                elif video['views_per_hour'] > 1500:
                    output.append("💡 KEY TAKEAWAY: Strong performer - study keyword usage")
                else:
                    output.append("💡 KEY TAKEAWAY: Standard performance - note title approach")
                output.append("")

                output.append("─" * 70)
                output.append("")

            # Channel insights
            if insights:
                output.append(f"📈 CHANNEL INSIGHTS:")
                output.append(f"   Avg VPH: {insights.get('avg_views_per_hour', 0):.1f}")
                output.append(f"   Avg Duration: {insights.get('avg_duration_minutes', 0):.1f} min")
                output.append(f"   Total Views: {insights.get('total_views', 0):,}")
                output.append("")

        # Title analysis
        title_analysis = self.analyze_titles(data)

        output.append("═" * 70)
        output.append("🎯 CROSS-CHANNEL TITLE ANALYSIS")
        output.append("═" * 70)
        output.append("")

        if title_analysis['common_keywords']:
            output.append("🔑 Most Common Keywords:")
            for keyword, count in title_analysis['common_keywords'][:10]:
                output.append(f"   • {keyword}: {count} times")
            output.append("")

        if title_analysis['name_mentions']:
            output.append("👤 Name Mentions:")
            for name, count in title_analysis['name_mentions'].items():
                output.append(f"   • {name}: {count} videos")
            output.append("")

        if title_analysis['emotional_triggers']:
            output.append("🔥 Emotional Triggers:")
            for trigger, count in title_analysis['emotional_triggers'].items():
                output.append(f"   • {trigger}: {count} videos")
            output.append("")

        output.append(f"📏 Avg Title Length: {title_analysis['avg_title_length']} characters")
        output.append(f"🔠 Avg ALL CAPS Words: {title_analysis['all_caps_words_avg']} per title")
        output.append("")

        output.append("═" * 70)

        return "\n".join(output)


# ============================================================================
# TESTING & DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    """
    Test the YouTube competitor tracker with real API calls.
    """
    import config
    from utils.settings_manager import CompetitorManager

    print("=" * 70)
    print("📺 TESTING YOUTUBE COMPETITOR TRACKER")
    print("=" * 70)
    print()
    
    # Load competitors from settings
    comp_mgr = CompetitorManager()
    active_competitors = comp_mgr.get_active()
    
    if not active_competitors:
        print("⚠️  No active competitors found. Add some at http://localhost:5000/settings")
        exit(1)
    
    # Create dict for tracker
    competitor_dict = {c['name']: c['channel_id'] for c in active_competitors}
    
    print(f"📺 Monitoring {len(active_competitors)} competitors:")
    for comp in active_competitors:
        print(f"   - {comp['name']} ({comp['channel_id']})")
    
    # Initialize tracker
    try:
        tracker = YouTubeCompetitorTracker(
            api_key=config.YOUTUBE_API_KEY,
            competitor_channels=competitor_dict
        )
        print(f"✅ YouTube tracker initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize YouTube tracker: {e}")
        print()
        print("Make sure you have:")
        print("1. Valid YOUTUBE_API_KEY in your .env file")
        print("2. YouTube Data API v3 enabled in Google Cloud Console")
        sys.exit(1)

    print("🔄 Starting collection...")
    print("(This may take a few seconds)")
    print()

    try:
        # Collect data
        data = tracker.collect(
            hours_back=48,
            videos_per_channel=3
        )

        # Show summary
        print()
        print("=" * 70)
        print("📊 RAW DATA SUMMARY")
        print("=" * 70)
        print(f"Total videos found: {data['total_videos_found']}")
        print(f"Channels monitored: {data['channels_monitored']}")
        print(f"Collection time: {data['timestamp']}")
        print()

        if data['competitor_data']:
            first_channel = data['competitor_data'][0]
            print(f"First channel: {first_channel['channel_name']}")
            if first_channel['videos']:
                video = first_channel['videos'][0]
                print(f"  Latest video: {video['title']}")
                print(f"  Views: {video['view_count']:,}")
                print(f"  VPH: {video['views_per_hour']:.1f}")
                print(f"  Rating: {video['performance_rating']}")
            print()

        # Title analysis
        print("=" * 70)
        print("📝 TITLE ANALYSIS")
        print("=" * 70)
        title_analysis = tracker.analyze_titles(data)
        print(f"Common keywords: {title_analysis['common_keywords'][:5]}")
        print(f"Name mentions: {title_analysis['name_mentions']}")
        print(f"Emotional triggers: {title_analysis['emotional_triggers']}")
        print()

        # Show formatted output
        print("=" * 70)
        print("📝 FORMATTED OUTPUT (For AI Prompts)")
        print("=" * 70)
        print()
        formatted = tracker.format_for_prompt(data)
        print(formatted)

        print()
        print("=" * 70)
        print("✅ YOUTUBE TRACKER TEST COMPLETE")
        print("=" * 70)
        print()

    except Exception as e:
        print()
        print(f"❌ ERROR during collection: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
