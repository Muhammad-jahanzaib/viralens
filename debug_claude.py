
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Mock config
sys.path.append(os.getcwd())
import config

from generators.claude_client import ClaudeTopicGenerator

# Mock User data
mock_research_data = {
    "google_trends": """
    GOOGLE TRENDS DATA
    " 'Meghan Markle' - Interest: +200% (Breakout)
    " 'Prince Harry' - Interest: +150% (Rising)
    """,
    "twitter": """
    TWITTER DATA
    "Meghan Markle's Netflix deal reportedly in trouble" (15k engagement)
    """,
    "reddit": """
    REDDIT DATA
    Timeline: "Meghan's project timeline shows pattern of failures" (450 upvotes)
    """,
    "youtube": """
    YOUTUBE COMPETITOR DATA
    Jessica Talks Tea: "Meghan EXPOSED" - 5,200 VPH
    """,
    "news": """
    NEWS DATA
    Daily Mail: "Meghan Markle's Netflix deal under scrutiny"
    """
}

def test_generation():
    print("Testing Claude Generation...")
    generator = ClaudeTopicGenerator(api_key=config.ANTHROPIC_API_KEY)
    
    try:
        result = generator.generate_topics(mock_research_data)
        topics = result.get('topic_recommendations', [])
        print(f"Generated {len(topics)} topics")
        for t in topics:
            print(f"- {t.get('title')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()
