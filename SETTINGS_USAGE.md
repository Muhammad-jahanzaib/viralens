# Settings Manager Usage Guide

Complete guide for managing YouTube competitors and research keywords dynamically.

## Quick Start

```python
from utils.settings_manager import CompetitorManager, KeywordManager

# Initialize managers
comp_manager = CompetitorManager()
kw_manager = KeywordManager()
```

## CompetitorManager

### Add Competitor (Auto Channel ID Detection)

```python
# Add competitor - Channel ID is auto-detected!
competitor = comp_manager.add(
    name="Jessica Talks Tea",
    url="https://www.youtube.com/@JessicaTalksTea",
    notes="Major competitor, posts daily"
)

# Returns:
# {
#   "id": 1,
#   "name": "Jessica Talks Tea",
#   "url": "https://www.youtube.com/@JessicaTalksTea",
#   "channel_id": "UCxxxxxxxxxx",  # Auto-detected!
#   "enabled": True,
#   "added_date": "2026-01-18T10:30:00",
#   "last_checked": "2026-01-18T10:30:00",
#   "status": "active",
#   "notes": "Major competitor, posts daily"
# }
```

### Supported URL Formats

The system automatically detects Channel IDs from:

```python
# Format 1: Direct Channel ID
"https://www.youtube.com/channel/UC1234567890abcdefg"

# Format 2: @Handle (NEW format) - Most common!
"https://www.youtube.com/@JessicaTalksTea"

# Format 3: Custom URL
"https://www.youtube.com/c/BBCNews"

# Format 4: Legacy username
"https://www.youtube.com/user/BBCNews"
```

### Get Competitors

```python
# Get all active competitors (enabled=True, has channel_id)
active = comp_manager.get_active()

# Get all competitors (including disabled)
all_comps = comp_manager.get_all()

# Get specific competitor by ID
competitor = comp_manager.get_by_id(1)
```

### Update Competitor

```python
# Update any field
comp_manager.update(1, {
    "name": "New Name",
    "notes": "Updated notes"
})

# Update URL (auto re-detects Channel ID)
comp_manager.update(1, {
    "url": "https://www.youtube.com/@NewChannel"
})
```

### Toggle Enable/Disable

```python
# Toggle enabled status
new_state = comp_manager.toggle_enabled(1)
# Returns: True or False
```

### Delete Competitor

```python
# Delete by ID
success = comp_manager.delete(1)
# Returns: True if deleted, False if not found
```

### Validate Channel ID

```python
# Check if Channel ID is valid
is_valid = comp_manager.validate_channel_id("UC1234567890abcdefg")
# Returns: True/False
```

## KeywordManager

### Add Keyword

```python
# Add new keyword
keyword = kw_manager.add("Kate Middleton", category="primary")

# Returns:
# {
#   "id": 5,
#   "keyword": "Kate Middleton",
#   "enabled": True,
#   "category": "primary",
#   "added_date": "2026-01-18T10:30:00"
# }
```

### Get Keywords

```python
# Get active keywords as strings
active_keywords = kw_manager.get_active()
# Returns: ["Meghan Markle", "Prince Harry", ...]

# Get keywords by category
primary = kw_manager.get_by_category("primary")
secondary = kw_manager.get_by_category("secondary")

# Get all keywords (full objects)
all_kw = kw_manager.get_all()
```

### Update Keyword

```python
# Update keyword
kw_manager.update(1, {
    "keyword": "Meghan Markle Sussex",
    "category": "primary"
})
```

### Toggle & Delete

```python
# Toggle enabled
new_state = kw_manager.toggle_enabled(1)

# Delete keyword
success = kw_manager.delete(5)
```

## Default Keywords

The system starts with these default keywords:

- **Primary**: Meghan Markle, Prince Harry
- **Secondary**: Archewell Foundation, Royal Family

## Data Files

```
data/
├── competitors.json       # Competitor data
├── keywords.json          # Keyword data
└── backups/              # Automatic backups
    ├── competitors.json.backup.YYYYMMDD_HHMMSS
    └── keywords.json.backup.YYYYMMDD_HHMMSS
```

## Features

### ✅ Automatic Backups
- Creates timestamped backup before every save
- Keeps last 5 backups automatically
- Backup location: `data/backups/`

### ✅ Thread-Safe
- Uses file locking (`filelock`)
- Safe for concurrent access
- Automatic lock timeout (10 seconds)

### ✅ Error Handling
- Handles corrupt JSON files (auto-backup and recreate)
- Validates YouTube URLs
- Handles YouTube API errors gracefully
- Comprehensive logging

### ✅ Auto Channel ID Detection
- Detects from 4 different URL formats
- Uses YouTube Data API for @handles
- Validates Channel IDs
- Re-detects when URL changes

## Integration with Research System

```python
# Get active competitors for YouTube collector
from utils.settings_manager import CompetitorManager
from collectors.youtube_collector import YouTubeCollector

comp_manager = CompetitorManager()
active_competitors = comp_manager.get_active()

# Pass to YouTube collector
channel_ids = [c['channel_id'] for c in active_competitors]
youtube_collector = YouTubeCollector(config.YOUTUBE_API_KEY)
youtube_data = youtube_collector.collect_from_channels(channel_ids)
```

```python
# Get active keywords for Google Trends
from utils.settings_manager import KeywordManager
from collectors.google_trends import GoogleTrendsCollector

kw_manager = KeywordManager()
active_keywords = kw_manager.get_active()

# Pass to Google Trends collector
trends_collector = GoogleTrendsCollector(keywords=active_keywords)
trends_data = trends_collector.collect()
```

## Error Messages

Common errors and solutions:

```python
# ValueError: "Could not detect YouTube Channel ID"
# - Check URL format
# - Verify channel exists and is public
# - Check YouTube API key is valid

# ValueError: "Keyword already exists"
# - Check for duplicates (case-insensitive)

# TimeoutError: "Could not acquire lock"
# - Another process is accessing the file
# - Wait and retry
```

## Logging

All operations are logged:

```python
# Enable logging to see detailed operations
from utils.logger import logger

# Logs include:
# - CRUD operations (add, update, delete)
# - Channel ID detection attempts
# - YouTube API calls
# - Backup creation
# - Errors with full context
```

## Example: Complete Workflow

```python
from utils.settings_manager import CompetitorManager, KeywordManager

# 1. Setup competitors
comp_manager = CompetitorManager()

# Add multiple competitors
competitors = [
    ("Jessica Talks Tea", "https://www.youtube.com/@JessicaTalksTea"),
    ("The Royal Grift", "https://www.youtube.com/@TheRoyalGrift"),
    ("River", "https://www.youtube.com/@RiverRoyalNews")
]

for name, url in competitors:
    try:
        comp_manager.add(name, url)
        print(f"✅ Added: {name}")
    except Exception as e:
        print(f"❌ Failed to add {name}: {e}")

# 2. Setup keywords
kw_manager = KeywordManager()

# Add custom keywords
custom_keywords = [
    ("Kate Middleton", "primary"),
    ("King Charles", "primary"),
    ("Royal Protocol", "secondary")
]

for keyword, category in custom_keywords:
    try:
        kw_manager.add(keyword, category=category)
        print(f"✅ Added keyword: {keyword}")
    except Exception as e:
        print(f"❌ Failed to add {keyword}: {e}")

# 3. Get active data for research
active_competitors = comp_manager.get_active()
active_keywords = kw_manager.get_active()

print(f"\n✅ Ready for research!")
print(f"   Competitors: {len(active_competitors)}")
print(f"   Keywords: {len(active_keywords)}")
```

## Testing

Run the test script to verify everything works:

```bash
python3 test_settings.py
```

This will:
- Test competitor management
- Test keyword management
- Verify Channel ID auto-detection
- Create sample data files
- Show all functionality
