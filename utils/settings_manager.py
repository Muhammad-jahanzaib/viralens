import json
import os
import re
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Any

from googleapiclient.discovery import build # type: ignore
from googleapiclient.errors import HttpError # type: ignore

from config import YOUTUBE_API_KEY
from utils.logger import logger


class CompetitorManager:
    """
    Manages YouTube competitors with JSON file storage and automatic Channel ID detection.
    """

    def __init__(self, file_path: str = "data/competitors.json"):
        """
        Initialize manager.
        
        Args:
            file_path: Path to the JSON file storing competitors.
        """
        self.file_path = file_path
        self._ensure_file_exists()
        self.competitors: List[Dict[str, Any]] = self.load()

    def _ensure_file_exists(self) -> None:
        """Create file with empty array if it doesn't exist."""
        if not os.path.exists(self.file_path):
            try:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump({"competitors": []}, f, indent=2)
                logger.info(f"Created new competitors file at {self.file_path}")
            except Exception as e:
                logger.error(f"Failed to create competitors file: {e}")
                raise

    def load(self) -> List[Dict[str, Any]]:
        """
        Read from JSON file.
        
        Returns:
            List of competitor dictionaries.
        """
        if not os.path.exists(self.file_path):
            logger.warning(f"File {self.file_path} not found.")
            return []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("competitors", [])
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {self.file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading competitors from {self.file_path}: {e}")
            return []

    def save(self, competitors: List[Dict[str, Any]]) -> bool:
        """
        Write to JSON with indent=2 and create a backup.
        
        Args:
            competitors: List of competitor dictionaries to save.
            
        Returns:
            True on success, False on error.
        """
        try:
            # Create backup
            if os.path.exists(self.file_path):
                backup_path = f"{self.file_path}.backup"
                shutil.copy2(self.file_path, backup_path)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({"competitors": competitors}, f, indent=2)
            
            # Update internal state
            self.competitors = competitors
            return True
        except Exception as e:
            logger.error(f"Error saving competitors to {self.file_path}: {e}")
            return False

    def add(self, name: str, url: str, description: str = "", channel_id: str = None, enabled: bool = True) -> Dict[str, Any]:
        """
        Add a new competitor.
        
        Args:
            name: Competitor name.
            url: YouTube channel URL.
            description: Optional description.
            channel_id: Optional manual channel ID (skips detection).
            enabled: Initial enabled state.
            
        Returns:
            The newly created competitor dictionary.
            
        Raises:
            ValueError: If inputs are invalid or channel ID detection fails.
        """
        if not name or not url:
            raise ValueError("Name and URL are required")

        logger.info(f"Adding new competitor: {name} ({url})")

        if not channel_id:
            try:
                channel_id = self._find_channel_id(url)
            except Exception as e:
                logger.error(f"Failed to detect channel ID for {url}: {e}")
                raise ValueError(f"Could not detect Channel ID: {e}")
        else:
             logger.info(f"Using manual Channel ID: {channel_id}")

        # Generate new ID
        new_id = 1
        if self.competitors:
            new_id = max(c["id"] for c in self.competitors) + 1

        now = datetime.utcnow().isoformat() + 'Z'

        new_competitor = {
            "id": new_id,
            "name": name,
            "url": url,
            "channel_id": channel_id,
            "enabled": enabled,
            "description": description,
            "added_date": now,
            "last_checked": now
        }

        self.competitors.append(new_competitor)
        if self.save(self.competitors):
            logger.info(f"Successfully added competitor: {name} (ID: {new_id})")
            return new_competitor
        else:
            # Revert change if save fails
            self.competitors.pop()
            raise IOError("Failed to save new competitor")

    def update(self, competitor_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing competitor.
        
        Args:
            competitor_id: ID of the competitor to update.
            data: Dictionary of fields to update.
            
        Returns:
            True if found and updated, False otherwise.
        """
        for i, competitor in enumerate(self.competitors):
            if competitor["id"] == competitor_id:
                logger.info(f"Updating competitor ID {competitor_id}")
                
                # Update fields
                updated_competitor = competitor.copy()
                updated_competitor.update(data)
                
                # Check if URL changed and need to re-detect ID
                if "url" in data and data["url"] != competitor["url"]:
                    try:
                        logger.info(f"URL changed for ID {competitor_id}, re-detecting channel ID...")
                        updated_competitor["channel_id"] = self._find_channel_id(data["url"])
                    except Exception as e:
                        logger.error(f"Failed to update channel ID for new URL: {e}")
                        # Keep old ID or raise? proper behavior is probably to not update if invalid. 
                        # But requirements say "If url changed, re-detect". 
                        # I will assume if detection fails, we shouldn't save.
                        return False

                updated_competitor["last_checked"] = datetime.utcnow().isoformat() + 'Z'
                
                # don't allow changing ID
                updated_competitor["id"] = competitor_id
                
                self.competitors[i] = updated_competitor
                return self.save(self.competitors)
        
        logger.warning(f"Competitor ID {competitor_id} not found for update")
        return False

    def delete(self, competitor_id: int) -> bool:
        """
        Delete a competitor by ID.
        
        Args:
            competitor_id: ID of the competitor.
            
        Returns:
            True if found and deleted, False otherwise.
        """
        initial_len = len(self.competitors)
        self.competitors = [c for c in self.competitors if c["id"] != competitor_id]
        
        if len(self.competitors) < initial_len:
            logger.info(f"Deleted competitor ID {competitor_id}")
            return self.save(self.competitors)
        
        logger.warning(f"Competitor ID {competitor_id} not found for deletion")
        return False

    def toggle_enabled(self, competitor_id: int) -> Optional[bool]:
        """
        Toggle the enabled status of a competitor.
        
        Args:
            competitor_id: ID of the competitor.
            
        Returns:
            New enabled state (True/False), or None if not found.
        """
        for i, competitor in enumerate(self.competitors):
            if competitor["id"] == competitor_id:
                new_state = not competitor.get("enabled", True)
                self.competitors[i]["enabled"] = new_state
                self.save(self.competitors)
                logger.info(f"Toggled competitor ID {competitor_id} to {new_state}")
                return new_state
        
        return None

    def get_active(self) -> List[Dict[str, Any]]:
        """
        Get all enabled competitors with valid channel IDs.
        
        Returns:
            List of active competitors.
        """
        return [c for c in self.competitors if c.get("enabled", True) and c.get("channel_id")]

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all competitors.
        
        Returns:
            List of all competitors.
        """
        return self.competitors

    def get_by_id(self, competitor_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single competitor by ID.
        
        Args:
            competitor_id: ID of the competitor.
            
        Returns:
            Competitor dictionary or None.
        """
        for competitor in self.competitors:
            if competitor["id"] == competitor_id:
                return competitor
        return None

    def _find_channel_id(self, url: str) -> str:
        """
        Extract Channel ID from YouTube URL using regex or API.
        
        Args:
            url: YouTube channel URL.
            
        Returns:
            Channel ID string.
            
        Raises:
            ValueError: If channel ID cannot be found.
        """
        logger.debug(f"Attempting to find channel ID for: {url}")
        
        # 1. Direct regex for youtube.com/channel/UC...
        channel_pattern = r"youtube\.com/channel/(UC[\w-]+)"
        match = re.search(channel_pattern, url)
        if match:
            return match.group(1)

        # 2. API Search for handle, user, or c
        if not YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY not configured")

        try:
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
            
            # Extract handle/username/c from URL
            # Handles: youtube.com/@handle
            handle_match = re.search(r"youtube\.com/(@[\w-]+)", url)
            
            # User: youtube.com/user/username
            user_match = re.search(r"youtube\.com/user/([\w-]+)", url)
            
            # Custom URL: youtube.com/c/name or just youtube.com/name
            # Note: Detecting custom URLs is tricky, usually we search for the last path segment
            
            query = ""
            if handle_match:
                query = handle_match.group(1)
            elif user_match:
                query = user_match.group(1)
            else:
                # Fallback: take the last part of the URL
                # Remove trailing slash
                clean_url = url.rstrip('/')
                query = clean_url.split('/')[-1]
            
            logger.debug(f"Searching YouTube API for query: {query}")
            
            request = youtube.search().list(
                part='snippet',
                q=query,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            
            if not response.get('items'):
                raise ValueError(f"No channel found for query: {query}")
            
            channel_id = response['items'][0]['snippet']['channelId']
            logger.info(f"Found channel ID {channel_id} for URL {url}")
            return channel_id

        except HttpError as e:
            logger.error(f"YouTube API Error: {e}")
            raise ValueError(f"YouTube API Error: {e}")
        except Exception as e:
            logger.error(f"Error extracting channel ID: {e}")
            raise ValueError(f"Error extracting channel ID: {e}")


class KeywordManager:
    """
    Manages research keywords with JSON file storage.
    """

    def __init__(self, file_path: str = "data/keywords.json"):
        """
        Initialize manager.
        
        Args:
            file_path: Path to the JSON file storing keywords.
        """
        self.file_path = file_path
        self._ensure_file_exists()
        self.keywords: List[Dict[str, Any]] = self.load()

    def _ensure_file_exists(self) -> None:
        """Create file with empty keywords if it doesn't exist."""
        if not os.path.exists(self.file_path):
            try:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

                # Create empty keywords file - user must add their own niche-specific keywords
                initial_data = []

                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump({"keywords": initial_data}, f, indent=2)
                logger.info(f"Created new empty keywords file at {self.file_path}")
                logger.warning("⚠️  Keywords file is empty. Please add keywords via the web interface or manually edit data/keywords.json")
            except Exception as e:
                logger.error(f"Failed to create keywords file: {e}")
                raise

    def load(self) -> List[Dict[str, Any]]:
        """
        Read from JSON file.
        
        Returns:
            List of keyword dictionaries.
        """
        if not os.path.exists(self.file_path):
            logger.warning(f"File {self.file_path} not found.")
            return []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("keywords", [])
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {self.file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading keywords from {self.file_path}: {e}")
            return []

    def save(self, keywords: List[Dict[str, Any]]) -> bool:
        """
        Write to JSON with indent=2 and create a backup.
        
        Args:
            keywords: List of keyword dictionaries to save.
            
        Returns:
            True on success, False on error.
        """
        try:
            # Create backup
            if os.path.exists(self.file_path):
                backup_path = f"{self.file_path}.backup"
                shutil.copy2(self.file_path, backup_path)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({"keywords": keywords}, f, indent=2)
            
            # Update internal state
            self.keywords = keywords
            return True
        except Exception as e:
            logger.error(f"Error saving keywords to {self.file_path}: {e}")
            return False

    def add(self, keyword: str, category: str = "primary") -> Dict[str, Any]:
        """
        Add a new keyword.
        
        Args:
            keyword: The research keyword.
            category: "primary" or "secondary".
            
        Returns:
            The newly created keyword dictionary.
            
        Raises:
            ValueError: If inputs are invalid or duplicate exists.
        """
        if not keyword:
            raise ValueError("Keyword cannot be empty")
            
        category = category.lower()
        if category not in ["primary", "secondary"]:
            raise ValueError("Category must be 'primary' or 'secondary'")

        # Check for duplicates (case-insensitive)
        if any(k["keyword"].lower() == keyword.lower() for k in self.keywords):
            raise ValueError(f"Keyword '{keyword}' already exists")

        logger.info(f"Adding new keyword: {keyword} ({category})")

        # Generate new ID
        new_id = 1
        if self.keywords:
            new_id = max(k["id"] for k in self.keywords) + 1

        now = datetime.utcnow().isoformat() + 'Z'

        new_item = {
            "id": new_id,
            "keyword": keyword,
            "category": category,
            "enabled": True,
            "added_date": now
        }

        self.keywords.append(new_item)
        if self.save(self.keywords):
            logger.info(f"Successfully added keyword: {keyword} (ID: {new_id})")
            return new_item
        else:
            self.keywords.pop()
            raise IOError("Failed to save new keyword")

    def update(self, keyword_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing keyword.
        
        Args:
            keyword_id: ID of the keyword to update.
            data: Dictionary of fields to update.
            
        Returns:
            True if found and updated, False otherwise.
        """
        for i, item in enumerate(self.keywords):
            if item["id"] == keyword_id:
                logger.info(f"Updating keyword ID {keyword_id}")
                
                updated_item = item.copy()
                updated_item.update(data)
                
                # Check validation if updating keyword or category
                if "keyword" in data:
                    new_kw = data["keyword"]
                    if not new_kw:
                        logger.error("Attempted to set empty keyword")
                        return False
                    # Check duplicates (excluding self)
                    if any(k["keyword"].lower() == new_kw.lower() and k["id"] != keyword_id for k in self.keywords):
                        logger.error(f"Duplicate keyword '{new_kw}'")
                        return False

                if "category" in data:
                    if data["category"] not in ["primary", "secondary"]:
                        logger.error(f"Invalid category '{data['category']}'")
                        return False

                updated_item["id"] = keyword_id # Prevent ID change
                self.keywords[i] = updated_item
                return self.save(self.keywords)
        
        logger.warning(f"Keyword ID {keyword_id} not found for update")
        return False

    def delete(self, keyword_id: int) -> bool:
        """
        Delete a keyword by ID.
        
        Args:
            keyword_id: ID of the keyword.
            
        Returns:
            True if found and deleted, False otherwise.
        """
        initial_len = len(self.keywords)
        self.keywords = [k for k in self.keywords if k["id"] != keyword_id]
        
        if len(self.keywords) < initial_len:
            logger.info(f"Deleted keyword ID {keyword_id}")
            return self.save(self.keywords)
        
        logger.warning(f"Keyword ID {keyword_id} not found for deletion")
        return False

    def toggle_enabled(self, keyword_id: int) -> Optional[bool]:
        """
        Toggle the enabled status of a keyword.
        
        Args:
            keyword_id: ID of the keyword.
            
        Returns:
            New enabled state (True/False), or None if not found.
        """
        for i, item in enumerate(self.keywords):
            if item["id"] == keyword_id:
                new_state = not item.get("enabled", True)
                self.keywords[i]["enabled"] = new_state
                self.save(self.keywords)
                logger.info(f"Toggled keyword ID {keyword_id} to {new_state}")
                return new_state
        
        return None

    def get_active(self) -> List[str]:
        """
        Get all enabled keywords as strings.
        
        Returns:
            List of keyword strings.
        """
        return [k["keyword"] for k in self.keywords if k.get("enabled", True)]

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all keywords.
        
        Returns:
            List of all keyword dictionaries.
        """
        return self.keywords

    def get_by_id(self, keyword_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single keyword by ID.
        
        Args:
            keyword_id: ID of the keyword.
            
        Returns:
            Keyword dictionary or None.
        """
        for item in self.keywords:
            if item["id"] == keyword_id:
                return item
        return None

    def get_by_category(self, category: str) -> List[str]:
        """
        Get enabled keywords for a specific category.

        Args:
            category: "primary" or "secondary".

        Returns:
            List of keyword strings.
        """
        return [
            k["keyword"] for k in self.keywords
            if k.get("enabled", True) and k.get("category") == category
        ]

    def get_optimized_keywords(self, max_keywords: int = None) -> List[str]:
        """
        Get optimized keyword list for API efficiency.

        Prioritizes:
        1. Primary keywords first
        2. Recently added keywords
        3. Twitter-safe keywords (no operator words)

        Args:
            max_keywords: Maximum keywords to return (default: system config or 8)

        Returns:
            List of keyword strings, optimized for API efficiency

        Example:
            >>> km = KeywordManager()
            >>> keywords = km.get_optimized_keywords(max_keywords=5)
            >>> print(keywords)  # Top 5 optimized keywords
        """
        if max_keywords is None:
            max_keywords = SYSTEM_CONFIG.get('collection_settings.max_keywords', 8)
            
        keywords = self.load()

        # Filter enabled only
        enabled = [k for k in keywords if k.get('enabled', True)]

        if not enabled:
            logger.warning("No enabled keywords found")
            return []

        # Score keywords
        scored = []
        for kw in enabled:
            score = 0

            # Primary category gets bonus
            if kw.get('category') == 'primary':
                score += 10

            # Recent additions get bonus (decay over time)
            try:
                added_date_str = kw.get('added_date', '')
                if added_date_str:
                    # Remove 'Z' timezone indicator if present
                    added_date_str = added_date_str.replace('Z', '')
                    added_date = datetime.fromisoformat(added_date_str)
                    days_old = (datetime.utcnow() - added_date).days
                    # Bonus decreases as keyword ages (max 10 points for new, 0 after 10 days)
                    score += max(0, 10 - days_old)
            except Exception as e:
                logger.debug(f"Could not parse date for '{kw.get('keyword')}': {e}")
                pass

            # Twitter-safe keywords get bonus (no operator words)
            keyword_text = kw.get('keyword', '').lower()
            if not any(op in keyword_text for op in [' and ', ' or ', ' not ', ' to ', ' from ']):
                score += 5
            else:
                logger.debug(f"Keyword '{kw.get('keyword')}' contains operator words")

            scored.append((score, kw))

        # Sort by score (highest first)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Take top N
        optimized = [kw['keyword'] for score, kw in scored[:max_keywords]]

        logger.info(f"🎯 Optimized keywords: {len(enabled)} enabled → {len(optimized)} selected (max: {max_keywords})")
        for i, (score, kw) in enumerate(scored[:max_keywords]):
            logger.debug(f"  {i+1}. {kw['keyword']} (score: {score}, category: {kw.get('category')})")

        return optimized

    def validate_twitter_compatibility(self, keyword: str) -> Dict[str, Any]:
        """
        Check if keyword is Twitter API compatible.

        Twitter API treats certain words like "and", "or", "not" as operators,
        which can cause syntax errors. This method detects these issues.

        Args:
            keyword: Keyword string to validate

        Returns:
            Dict with:
            - compatible (bool): True if compatible, False otherwise
            - issue (str or None): Description of the issue
            - suggestion (str or None): Suggested fix

        Example:
            >>> km = KeywordManager()
            >>> result = km.validate_twitter_compatibility("car and tuning")
            >>> print(result)
            {
                'compatible': False,
                'issue': "Contains Twitter operator word 'and'",
                'suggestion': 'car tuning'
            }
        """
        keyword_lower = keyword.lower()

        # Check for problematic operators
        operators = ['and', 'or', 'not', 'to', 'from']

        for op in operators:
            if f' {op} ' in keyword_lower:
                # Remove the operator to create suggestion
                suggestion = keyword_lower
                for remove_op in operators:
                    suggestion = suggestion.replace(f' {remove_op} ', ' ')
                # Clean up multiple spaces
                suggestion = ' '.join(suggestion.split())

                return {
                    'compatible': False,
                    'issue': f"Contains Twitter operator word '{op}'",
                    'suggestion': suggestion
                }

        return {
            'compatible': True,
            'issue': None,
            'suggestion': None
        }


from utils.system_config import SYSTEM_CONFIG

