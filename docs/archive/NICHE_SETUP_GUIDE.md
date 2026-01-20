# Universal Niche Configuration Guide

This system works for **ANY YouTube content niche**. Simply configure your keywords and competitors, and the AI will automatically adapt to your niche.

## How It Works

```
Your Keywords → Data Collection → AI Auto-Detects Niche → Generates Topics for YOUR Niche
```

The AI prompt is designed to be **niche-agnostic**:
- It analyzes the keywords you provide
- Detects the niche from the data
- Adapts its content strategy accordingly
- Generates topics specific to YOUR niche

## Quick Setup for Any Niche

### Option 1: Use Web Interface (Easiest)

```bash
python3 app.py
# Navigate to http://127.0.0.1:8000
# Go to Settings → Keywords → Add your niche keywords
# Go to Settings → Competitors → Add your competitor channels
```

### Option 2: Edit JSON Files Manually

**Edit `data/keywords.json`:**
```json
{
  "keywords": [
    {
      "id": 1,
      "keyword": "YOUR_KEYWORD_1",
      "category": "primary",
      "enabled": true,
      "added_date": "2026-01-19T00:00:00.000000Z"
    },
    {
      "id": 2,
      "keyword": "YOUR_KEYWORD_2",
      "category": "primary",
      "enabled": true,
      "added_date": "2026-01-19T00:00:00.000000Z"
    }
  ]
}
```

**Edit `data/competitors.json`:**
```json
{
  "competitors": [
    {
      "id": 1,
      "name": "Competitor Name",
      "url": "https://youtube.com/@handle",
      "channel_id": "UCxxxxxxxxx",
      "enabled": true,
      "description": "Why tracking this channel",
      "added_date": "2026-01-19T00:00:00.000000Z"
    }
  ]
}
```

**Edit `config.py`:**
```python
REDDIT_SUBREDDIT = "your_subreddit"  # Update to your niche's subreddit
```

### Option 3: Use Setup Script

```bash
python3 setup_niche.py
# Follow the interactive prompts
```

## Example Configurations

### Tech/AI Niche

**Keywords:** ChatGPT, AI News, OpenAI, Tech Layoffs, Silicon Valley
**Competitors:** MKBHD, Linus Tech Tips, Marques Brownlee
**Subreddit:** r/technology
**Result:** AI and tech-focused video topics

### Finance/Investing Niche

**Keywords:** Bitcoin, Stock Market, Cryptocurrency, Inflation, Fed Meeting
**Competitors:** Graham Stephan, Meet Kevin, Andrei Jikh
**Subreddit:** r/investing
**Result:** Finance and investment-focused topics

### Gaming Niche

**Keywords:** Fortnite, Call of Duty, Gaming News, Esports, Game Reviews
**Competitors:** PewDiePie, Ninja, Shroud
**Subreddit:** r/gaming
**Result:** Gaming-focused video topics

### Cooking Niche

**Keywords:** Easy Recipes, Meal Prep, Cooking Tips, Healthy Eating
**Competitors:** Binging with Babish, Joshua Weissman
**Subreddit:** r/Cooking
**Result:** Cooking and recipe-focused topics

### Fitness Niche

**Keywords:** Workout Routine, Weight Loss, Gym Tips, Protein, Nutrition
**Competitors:** Athlean-X, Jeff Nippard, Jeremy Ethier
**Subreddit:** r/Fitness
**Result:** Fitness and health-focused topics

## How the AI Adapts

The AI prompt includes this instruction:

> "First, identify the dominant niche/topic from the input data (e.g., Royal Family, Automotive, Tech, Finance, etc.). Adapt your content strategy to fit the audience psychology of that specific niche."

This means:
- You configure keywords about YOUR niche
- System collects data about YOUR keywords
- AI sees the data and automatically detects YOUR niche
- AI generates topics tailored to YOUR niche's audience

## Current Configuration

Your system is currently configured for: **Royal Family Niche**
- Keywords: Meghan Markle, Prince Harry, Royal Family, etc.
- Competitors: Royal Family YouTube channels
- Subreddit: r/SaintMeghanMarkle

To change to a different niche, simply update the configuration files with your desired niche's keywords and competitors.

## Verification

After configuring your niche, run:

```bash
python3 -c "
from utils.settings_manager import KeywordManager
kw = KeywordManager()
keywords = [k['keyword'] for k in kw.get_optimized_keywords(max_keywords=8)]
print('Active Keywords:', keywords)
print('These keywords define your niche!')
"
```

Then run a research job:

```bash
python3 main.py --save
```

The generated topics will match your configured niche!
