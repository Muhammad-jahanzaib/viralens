#!/usr/bin/env python3
"""
YouTube Research Automation - Onboarding Script
Helps new users configure the system for their specific niche
"""

import json
import os
import sys
import re
from datetime import datetime
from typing import List, Dict

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def main():
    clear_screen()

    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  YouTube Research Automation - First Time Setup".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    print()
    print("Welcome! This script will help you configure the system for YOUR niche.")
    print()
    print("The system works for ANY YouTube content niche:")
    print("  • Tech & AI")
    print("  • Finance & Investing")
    print("  • Gaming")
    print("  • Cooking")
    print("  • Fitness")
    print("  • ...or ANY other niche you can think of!")
    print()

    input("Press Enter to continue...")

    # Step 1: Choose setup method
    clear_screen()
    print_header("Step 1: Choose Your Setup Method")

    print("How would you like to configure your niche?")
    print()
    print("1. Quick Setup (Choose from popular niches)")
    print("2. Custom Setup (Enter your own keywords)")
    print("3. Import from YouTube Channel (Analyze your channel)")
    print("4. Exit")
    print()

    choice = input("Enter your choice (1-4): ").strip()

    if choice == "1":
        quick_setup()
    elif choice == "2":
        custom_setup()
    elif choice == "3":
        import_from_channel()
    else:
        print("\nSetup cancelled. Run 'python3 onboard.py' to try again.")
        sys.exit(0)

def quick_setup():
    """Quick setup with pre-configured templates"""
    clear_screen()
    print_header("Quick Setup - Choose Your Niche")

    templates = {
        "1": {
            "name": "Tech & AI",
            "icon": "💻",
            "keywords": [
                {"keyword": "ChatGPT", "category": "primary"},
                {"keyword": "AI News", "category": "primary"},
                {"keyword": "OpenAI", "category": "primary"},
                {"keyword": "Tech Layoffs", "category": "primary"},
                {"keyword": "Silicon Valley", "category": "primary"},
                {"keyword": "Apple Event", "category": "secondary"},
                {"keyword": "Google AI", "category": "secondary"},
                {"keyword": "Tech Trends 2026", "category": "secondary"},
            ],
            "subreddit": "technology",
            "example_competitors": ["MKBHD", "Linus Tech Tips", "Marques Brownlee"]
        },
        "2": {
            "name": "Finance & Investing",
            "icon": "💰",
            "keywords": [
                {"keyword": "Bitcoin", "category": "primary"},
                {"keyword": "Stock Market", "category": "primary"},
                {"keyword": "Cryptocurrency", "category": "primary"},
                {"keyword": "Inflation", "category": "primary"},
                {"keyword": "Fed Meeting", "category": "primary"},
                {"keyword": "Real Estate Market", "category": "secondary"},
                {"keyword": "Trading Strategies", "category": "secondary"},
                {"keyword": "Investing Tips", "category": "secondary"},
            ],
            "subreddit": "investing",
            "example_competitors": ["Graham Stephan", "Meet Kevin", "Andrei Jikh"]
        },
        "3": {
            "name": "Gaming",
            "icon": "🎮",
            "keywords": [
                {"keyword": "Fortnite", "category": "primary"},
                {"keyword": "Call of Duty", "category": "primary"},
                {"keyword": "Gaming News", "category": "primary"},
                {"keyword": "Esports", "category": "primary"},
                {"keyword": "Game Reviews", "category": "primary"},
                {"keyword": "PlayStation", "category": "secondary"},
                {"keyword": "Xbox", "category": "secondary"},
                {"keyword": "Nintendo Switch", "category": "secondary"},
            ],
            "subreddit": "gaming",
            "example_competitors": ["PewDiePie", "Ninja", "Shroud"]
        },
        "4": {
            "name": "Cooking & Food",
            "icon": "🍳",
            "keywords": [
                {"keyword": "Easy Recipes", "category": "primary"},
                {"keyword": "Meal Prep", "category": "primary"},
                {"keyword": "Cooking Tips", "category": "primary"},
                {"keyword": "Healthy Eating", "category": "primary"},
                {"keyword": "Baking", "category": "secondary"},
                {"keyword": "Chef Skills", "category": "secondary"},
                {"keyword": "Food Science", "category": "secondary"},
            ],
            "subreddit": "Cooking",
            "example_competitors": ["Binging with Babish", "Joshua Weissman", "Ethan Chlebowski"]
        },
        "5": {
            "name": "Fitness & Health",
            "icon": "💪",
            "keywords": [
                {"keyword": "Workout Routine", "category": "primary"},
                {"keyword": "Weight Loss", "category": "primary"},
                {"keyword": "Gym Tips", "category": "primary"},
                {"keyword": "Protein", "category": "primary"},
                {"keyword": "Nutrition", "category": "primary"},
                {"keyword": "Bodybuilding", "category": "secondary"},
                {"keyword": "Cardio Exercises", "category": "secondary"},
                {"keyword": "Muscle Gain", "category": "secondary"},
            ],
            "subreddit": "Fitness",
            "example_competitors": ["Athlean-X", "Jeff Nippard", "Jeremy Ethier"]
        },
        "6": {
            "name": "Business & Entrepreneurship",
            "icon": "📈",
            "keywords": [
                {"keyword": "Startup", "category": "primary"},
                {"keyword": "Business Ideas", "category": "primary"},
                {"keyword": "Entrepreneurship", "category": "primary"},
                {"keyword": "Side Hustle", "category": "primary"},
                {"keyword": "E-commerce", "category": "primary"},
                {"keyword": "Marketing Strategies", "category": "secondary"},
                {"keyword": "Business Growth", "category": "secondary"},
                {"keyword": "Passive Income", "category": "secondary"},
            ],
            "subreddit": "Entrepreneur",
            "example_competitors": ["Ali Abdaal", "Pat Flynn", "Gary Vaynerchuk"]
        }
    }

    print("Available Niches:\n")
    for key, template in templates.items():
        print(f"{key}. {template['icon']} {template['name']}")
        print(f"   Keywords: {', '.join([k['keyword'] for k in template['keywords'][:3]])}...")
        print(f"   Subreddit: r/{template['subreddit']}")
        print()

    choice = input("Choose your niche (1-6): ").strip()

    if choice in templates:
        template = templates[choice]

        clear_screen()
        print_header(f"Selected: {template['icon']} {template['name']}")

        print("Configuration Preview:")
        print()
        print(f"📊 Keywords ({len(template['keywords'])}):")
        for i, kw in enumerate(template['keywords'], 1):
            print(f"   {i}. {kw['keyword']} ({kw['category']})")

        print()
        print(f"📱 Subreddit: r/{template['subreddit']}")
        print()
        print(f"🎥 Example Competitors: {', '.join(template['example_competitors'])}")
        print()

        confirm = input("Apply this configuration? (y/n): ").strip().lower()

        if confirm == 'y':
            apply_template(template)
        else:
            print("\n❌ Configuration cancelled.")
            main()
    else:
        print("\n❌ Invalid choice.")
        input("Press Enter to try again...")
        quick_setup()

def custom_setup():
    """Custom setup for any niche"""
    clear_screen()
    print_header("Custom Setup - Define Your Niche")

    print("Let's configure the system for your specific niche.\n")

    # Step 1: Niche name
    niche_name = input("What's your niche? (e.g., 'Travel Vlogging', 'Car Reviews'): ").strip()

    if not niche_name:
        print_warning("Niche name is required.")
        input("Press Enter to try again...")
        custom_setup()
        return

    # Step 2: Keywords
    print()
    print("Now, enter keywords your audience searches for.")
    print("Examples: 'best travel destinations', 'budget travel tips', etc.")
    print("(Enter at least 5 keywords, press Enter twice when done)\n")

    keywords = []
    while True:
        keyword = input(f"Keyword {len(keywords)+1} (or press Enter to finish): ").strip()

        if not keyword:
            if len(keywords) >= 5:
                break
            else:
                print_warning(f"Please enter at least {5 - len(keywords)} more keyword(s).")
                continue

        category = "primary" if len(keywords) < 5 else "secondary"
        keywords.append({"keyword": keyword, "category": category})

    # Step 3: Subreddit
    print()
    subreddit = input("Enter a relevant subreddit (without r/): ").strip()

    if not subreddit:
        print_warning("No subreddit entered. Using 'videos' as default.")
        subreddit = "videos"

    # Preview
    clear_screen()
    print_header(f"Configuration Preview: {niche_name}")

    print(f"📊 Keywords ({len(keywords)}):")
    for i, kw in enumerate(keywords, 1):
        print(f"   {i}. {kw['keyword']} ({kw['category']})")

    print()
    print(f"📱 Subreddit: r/{subreddit}")
    print()

    confirm = input("Apply this configuration? (y/n): ").strip().lower()

    if confirm == 'y':
        template = {
            "name": niche_name,
            "keywords": keywords,
            "subreddit": subreddit
        }
        apply_template(template)
    else:
        print("\n❌ Configuration cancelled.")
        main()

def import_from_channel():
    """Import configuration by analyzing a YouTube channel"""
    clear_screen()
    print_header("Import from YouTube Channel")

    print("This feature will analyze a YouTube channel to suggest keywords.")
    print()
    print_warning("This feature requires YouTube API access.")
    print_info("For now, please use Quick Setup or Custom Setup instead.")
    print()

    input("Press Enter to return to main menu...")
    main()

def apply_template(template):
    """Apply the selected template"""
    clear_screen()
    print_header("Applying Configuration...")

    # Step 1: Save keywords
    keywords_data = {"keywords": []}
    now = datetime.utcnow().isoformat() + 'Z'

    for i, kw in enumerate(template['keywords'], 1):
        keywords_data["keywords"].append({
            "id": i,
            "keyword": kw["keyword"],
            "category": kw["category"],
            "enabled": True,
            "added_date": now
        })

    os.makedirs("data", exist_ok=True)

    with open("data/keywords.json", 'w', encoding='utf-8') as f:
        json.dump(keywords_data, f, indent=2)

    print_success(f"Saved {len(template['keywords'])} keywords to data/keywords.json")

    # Step 2: Update config.py
    if os.path.exists("config.py"):
        with open("config.py", 'r', encoding='utf-8') as f:
            config_content = f.read()

        config_content = re.sub(
            r'REDDIT_SUBREDDIT\s*=\s*["\'][^"\']*["\']',
            f'REDDIT_SUBREDDIT = "{template["subreddit"]}"',
            config_content
        )

        with open("config.py", 'w', encoding='utf-8') as f:
            f.write(config_content)

        print_success(f"Updated subreddit to r/{template['subreddit']} in config.py")

    # Step 3: Clear competitors (user will add their own)
    with open("data/competitors.json", 'w', encoding='utf-8') as f:
        json.dump({"competitors": []}, f, indent=2)

    print_success("Reset competitors (you can add them via web interface)")

    # Done!
    clear_screen()
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🎉 Configuration Complete! 🎉".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    print()
    print(f"✅ Your system is now configured for: {template['name']}")
    print()
    print_header("Next Steps")

    print("1. (Optional) Add competitor YouTube channels:")
    print("   python3 app.py")
    print("   → Navigate to Settings → Competitors")
    print()

    print("2. Run your first research job:")
    print("   python3 main.py --save")
    print()

    print("3. View the generated report:")
    print("   The system will save HTML and JSON reports in data/research_reports/")
    print()

    print("4. The AI will automatically:")
    print("   ✓ Collect data about YOUR keywords")
    print("   ✓ Analyze YOUR niche's trends")
    print("   ✓ Generate video topics for YOUR audience")
    print()

    print_header("Tips for Best Results")

    print("• Add 5-10 competitor channels to track what's working in your niche")
    print("• Run research daily to catch trending topics early")
    print("• Review both 'Breaking/Trending' and 'Evergreen' topic suggestions")
    print("• Use the web interface (python3 app.py) to manage keywords easily")
    print()

    print("═"*70)
    print("  Ready to generate viral video topics for your niche!")
    print("═"*70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nPlease report this issue if it persists.")
        sys.exit(1)
