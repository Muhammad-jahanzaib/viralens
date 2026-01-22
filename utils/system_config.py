"""
System Configuration Manager
Loads and manages system-wide settings
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class SystemConfig:
    """Manages system-wide configuration settings"""
    
    def __init__(self, config_file: str = "data/system_config.json"):
        # Ensure absolute path relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_file = Path(os.path.join(base_dir, config_file))
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_file.exists():
            # Create default config
            default_config = {
                "collection_settings": {
                    "max_keywords": 4,
                    "twitter_min_engagement": 500,
                    "reddit_min_upvotes": 100,
                    "google_trends_fail_fast": True,
                    "enable_newsapi": False
                },
                "reddit_config": {
                    "auto_detect_subreddit": False,
                    "default_subreddit": "",
                    "fallback_subreddits": []
                },
                "performance_tuning": {
                    "parallel_collection_timeout": 90,
                    "max_retry_attempts": 1,
                    "retry_on_rate_limit": False
                },
                "niche_config": {
                    "name": "General",
                    "description": "General research",
                    "primary_subreddit": ""
                }
            }
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading system config: {e}")
            return {}
    
    def _save_config(self, config: Dict):
        """Save configuration to JSON file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def get(self, key_path: str, default=None):
        """Get config value using dot notation (e.g., 'collection_settings.max_keywords')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update(self, key_path: str, value: Any):
        """Update config value and save"""
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to parent
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set value
        current[keys[-1]] = value
        
        # Save
        self._save_config(self.config)
        # Update internal state
        self.config = config
    
    def get_all(self) -> Dict:
        """Get entire configuration"""
        return self.config


# Global instance
SYSTEM_CONFIG = SystemConfig()
