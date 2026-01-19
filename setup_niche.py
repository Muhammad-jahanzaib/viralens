#!/usr/bin/env python3
"""
Interactive Niche Setup Script
Helps users configure the system for their specific YouTube niche
"""

import json
import os
from datetime import datetime

def main():
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         YouTube Research Automation - Niche Setup             ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    print("This script will help you configure the system for YOUR niche.")
    print("The AI will automatically adapt to whatever niche you configure.")
    print()

    # Step 1: Choose setup method
    print("Choose your setup method:")
    print("1. Quick Setup (use a template)")
    print("2. Custom Setup (enter your own keywords)")
    print("3. Exit")
    print()

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        quick_setup()
    elif choice == "2":
        custom_setup()
    else:
        print("Setup cancelled.")
        return

def quick_setup():
    """Use pre-configured templates"""
    print("\n" + "="*60)
    print("QUICK SETUP - Choose a Template")
    print("="*60)

    templates = {
        "1": {
            "name": "Tech & AI",
            "keywords": [
                "ChatGPT", "AI News", "OpenAI", "Tech Layoffs",
                "Silicon Valley", "Apple Event", "Google AI", "Tech Trends"
            ],
            "subreddit": "technology"
        },
        "2": {
            "name": "Finance & Investing",
            "keywords": [
                "Bitcoin", "Stock Market", "Cryptocurrency", "Inflation",
                "Fed Meeting", "Real Estate", "Trading", "Investing"
            ],
            "subreddit": "investing"
        },
        "3": {
            "name": "Gaming",
            "keywords": [
                "Fortnite", "Call of Duty", "Gaming News", "Esports",
                "Game Reviews", "PlayStation", "Xbox", "Nintendo"
            ],
            "subreddit": "gaming"
        },
        "4": {
            "name": "Royal Family",
            "keywords": [
                "Meghan Markle", "Prince Harry", "Royal Family", "Archewell Foundation",
                "Duke and Duchess of Sussex", "King Charles", "Prince William"
            ],
            "subreddit": "SaintMeghanMarkle"
        },
        "5": {
            "name": "Cooking",
            "keywords": [
                "Easy Recipes", "Meal Prep", "Cooking Tips", "Healthy Eating",
                "Baking", "Chef Skills", "Food Science"
            ],
            "subreddit": "Cooking"
        },
        "6": {
            "name": "Fitness",
            "keywords": [
                "Workout Routine", "Weight Loss", "Gym Tips", "Protein",
                "Nutrition", "Bodybuilding", "Cardio", "Muscle Gain"
            ],
            "subreddit": "Fitness"
        }
    }

    print("\nAvailable Templates:")
    for key, template in templates.items():
        print(f"{key}. {template['name']}")
    print()

    choice = input("Choose template (1-6): ").strip()

    if choice in templates:
        template = templates[choice]
        print(f"\n✅ Selected: {template['name']}")
        print(f"Keywords: {', '.join(template['keywords'][:4])}...")
        print(f"Subreddit: r/{template['subreddit']}")
        print()

        confirm = input("Apply this configuration? (y/n): ").strip().lower()
        if confirm == 'y':
            apply_configuration(template['keywords'], template['subreddit'], template['name'])
        else:
            print("Configuration cancelled.")
    else:
        print("Invalid choice.")

def custom_setup():
    """Enter custom keywords"""
    print("\n" + "="*60)
    print("CUSTOM SETUP")
    print("="*60)
    print()
    print("Enter your niche keywords (one per line, press Enter twice when done):")
    print("Example: ChatGPT, AI News, Tech Layoffs")
    print()

    keywords = []
    while True:
        keyword = input(f"Keyword {len(keywords)+1} (or press Enter to finish): ").strip()
        if not keyword:
            break
        keywords.append(keyword)

    if not keywords:
        print("No keywords entered. Setup cancelled.")
        return

    print()
    subreddit = input("Enter Reddit subreddit (without r/): ").strip()

    print()
    niche_name = input("Enter niche name (e.g., 'Tech', 'Finance'): ").strip()

    print("\n" + "="*60)
    print("Configuration Preview:")
    print("="*60)
    print(f"Niche: {niche_name}")
    print(f"Keywords ({len(keywords)}): {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
    print(f"Subreddit: r/{subreddit}")
    print()

    confirm = input("Apply this configuration? (y/n): ").strip().lower()
    if confirm == 'y':
        apply_configuration(keywords, subreddit, niche_name)
    else:
        print("Configuration cancelled.")

def apply_configuration(keywords, subreddit, niche_name):
    """Apply the configuration"""
    print("\n" + "="*60)
    print("Applying Configuration...")
    print("="*60)

    # Create keywords.json
    keywords_data = {
        "keywords": []
    }

    now = datetime.utcnow().isoformat() + 'Z'
    for i, keyword in enumerate(keywords, 1):
        category = "primary" if i <= 5 else "secondary"
        keywords_data["keywords"].append({
            "id": i,
            "keyword": keyword,
            "category": category,
            "enabled": True,
            "added_date": now
        })

    # Save keywords.json
    keywords_file = "data/keywords.json"
    os.makedirs("data", exist_ok=True)

    with open(keywords_file, 'w', encoding='utf-8') as f:
        json.dump(keywords_data, f, indent=2)

    print(f"✅ Saved {len(keywords)} keywords to {keywords_file}")

    # Update config.py
    config_file = "config.py"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()

        # Update REDDIT_SUBREDDIT
        import re
        config_content = re.sub(
            r'REDDIT_SUBREDDIT\s*=\s*["\'][^"\']*["\']',
            f'REDDIT_SUBREDDIT = "{subreddit}"',
            config_content
        )

        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)

        print(f"✅ Updated subreddit to r/{subreddit} in config.py")

    # Clear competitors (user will add their own)
    competitors_file = "data/competitors.json"
    with open(competitors_file, 'w', encoding='utf-8') as f:
        json.dump({"competitors": []}, f, indent=2)

    print(f"✅ Reset competitors.json (add your competitors via web UI)")

    print("\n" + "="*60)
    print("✅ Configuration Applied Successfully!")
    print("="*60)
    print()
    print(f"Your system is now configured for: {niche_name}")
    print()
    print("Next Steps:")
    print("1. Add competitor YouTube channels:")
    print("   python3 app.py → Settings → Competitors")
    print()
    print("2. Run a research job:")
    print("   python3 main.py --save")
    print()
    print("3. The AI will automatically generate topics for YOUR niche!")
    print()

if __name__ == "__main__":
    main()
