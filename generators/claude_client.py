# -*- coding: utf-8 -*-
"""
Claude AI Topic Generator

This module uses Claude AI (Anthropic) to analyze research data and generate
viral YouTube video topic recommendations for any content niche.

Author: Royal Research Automation
Created: 2026-01-18
"""

import json
from typing import List, Dict, Optional
from datetime import datetime, timezone
from tenacity import retry, wait_exponential, stop_after_attempt

from anthropic import Anthropic
from utils.logger import logger
from generators.competitor_title_generator import CompetitorTitleGenerator


# Master prompt template for Claude AI
MASTER_PROMPT_TEMPLATE = """You are an expert YouTube content strategist and trend analyst. Your task is to analyze the provided research data (search trends, social discussions, competitor videos, news) and generate viral video topic recommendations tailored to the specific niche indicated by the data.

ANALYSIS INSTRUCTIONS:
1. First, identify the dominant niche/topic from the input data (e.g., Royal Family, Automotive, Tech, Finance, etc.).
2. Adapt your content strategy to fit the audience psychology of that specific niche.
3. Generate video ideas that are highly relevant to the provided data points.

STRATEGIC GOALS:
- Primary Goal: Generate 10 high-performing video topics (mix of Viral/Trending and Evergreen/Deep Dive).
- Title Strategy: Use proven click-through formulas relevant to the identified niche (Action verbs, Curiosity gaps, Name-dropping key entities).
- Audience Interaction: Focus on high-engagement angles (Debates, Reveals, Comparisons, "Truth about", "Why X is happening").

RESEARCH DATA FROM PAST 24 HOURS:

RESEARCH DATA FROM PAST 24 HOURS:

PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=
 GOOGLE TRENDS DATA
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
{google_trends}

PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=& TWITTER DATA
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
{twitter}

PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=4 REDDIT DATA
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
{reddit}

PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
= YOUTUBE COMPETITOR DATA
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
{youtube}

PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
= NEWS DATA
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
{news}

YOUR TASK:
Generate STRICTLY 10 YouTube video topic recommendations based on the research data above.

For each topic, provide:
1. Compelling video title (60-70 chars, follows formula)
2. Video type (Breaking/Trending or Evergreen/Deep Dive)
3. Hook (first 30 seconds script)
4. 6-8 key points to cover
5. Evidence sources (cite specific data from research)
6. Thumbnail concept (visual description)
7. Target duration
8. Viral potential assessment (HIGH/MEDIUM/LOW with reasoning)
9. Search keywords (5-7 for SEO)
10. Publishing priority (1-10, where 10 is urgent)

ALSO PROVIDE:
- Trending themes (3-5 major patterns across all data)
- Competitor insights (what they're doing, gaps to exploit)
- Timing recommendations (which topics are urgent vs evergreen)
- Risk warnings (topics to avoid, legal concerns, unverified claims)

Focus on:
- Deep analysis over surface-level news
- Evidence-based content derived from the provided data
- Unique angles not covered by the listed competitors
- Balance between high CTR (Click-Through Rate) and viewer retention
- SEO optimization for search traffic

OUTPUT FORMAT:
Please provide your response as a JSON object with the following structure:
{{
  "topic_recommendations": [
    {{
      "rank": 1,
      "title": "Video title here",
      "video_type": "Breaking/Trending or Evergreen/Deep Dive",
      "hook": "First 30 seconds script",
      "key_points": ["Point 1", "Point 2", "Point 3"],
      "evidence_sources": [
        {{"name": "Source Name", "platform": "Twitter/News/Reddit/YouTube", "hours_ago": 5, "url": "Direct link to source (required)"}}
      ],
      "thumbnail_concept": "Description",
      "target_duration": "10-14 minutes",
      "viral_potential": "HIGH/MEDIUM/LOW - reasoning",
      "search_keywords": ["keyword1", "keyword2"],
      "publishing_priority": 10
    }}
  ],
  "trending_themes": ["Theme 1", "Theme 2"],
  "competitor_insights": "Analysis here",
  "timing_recommendations": "Recommendations here",
  "risk_warnings": ["Warning 1", "Warning 2"]
}}"""


class ClaudeTopicGenerator:
    """
    Generate YouTube video topic recommendations using Claude AI.

    This class analyzes research data from multiple sources (Google Trends,
    Twitter, Reddit, YouTube, News) and generates viral video topic
    recommendations with detailed implementation guidance.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-latest",
        max_tokens: int = 8000,
        temperature: float = 1.0
    ):
        """
        Initialize the Claude topic generator.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum response length
            temperature: Creativity level (0-1, higher = more creative)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.session_tokens = {"input": 0, "output": 0}
        self.session_cost = 0.0
        self.title_generator = CompetitorTitleGenerator()

        logger.info(f"> Initialized Claude topic generator (model: {model})")

    @retry(
        wait=wait_exponential(min=4, max=60),
        stop=stop_after_attempt(2)
    )
    def generate_topics(self, research_data: Dict[str, str]) -> Dict:
        """
        Generate YouTube video topic recommendations from research data.

        Args:
            research_data: Dictionary with keys:
                - google_trends: Formatted Google Trends data
                - twitter: Formatted Twitter data
                - reddit: Formatted Reddit data
                - youtube: Formatted YouTube competitor data
                - news: Formatted News data

        Returns:
            Dictionary containing:
                - timestamp: Generation timestamp
                - model_used: Claude model used
                - tokens_used: Input/output token counts
                - cost_estimate: Cost in USD
                - topic_recommendations: List of 10 topic recommendations
                - trending_themes: List of trending themes
                - competitor_insights: Competitor analysis
                - timing_recommendations: Publishing timing advice
                - risk_warnings: List of warnings/concerns
        """
        logger.info("> Generating topics with Claude AI...")

        # Build the prompt
        prompt = MASTER_PROMPT_TEMPLATE.format(
            google_trends=research_data.get("google_trends", "No data available"),
            twitter=research_data.get("twitter", "No data available"),
            reddit=research_data.get("reddit", "No data available"),
            youtube=research_data.get("youtube", "No data available"),
            news=research_data.get("news", "No data available")
        )

        # Log prompt stats
        char_count = len(prompt)
        token_estimate = char_count // 4  # Rough estimate: 1 token H 4 chars
        logger.info(f"Prompt: {char_count:,} characters, ~{token_estimate:,} tokens")

        try:
            # Call Claude API
            logger.info(f"Calling Claude API (model: {self.model})...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract response text
            response_text = response.content[0].text

            # Extract token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Calculate cost
            # Claude 3.5 Sonnet pricing: $3/M input tokens, $15/M output tokens
            cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

            # Update session tracking
            self.session_tokens["input"] += input_tokens
            self.session_tokens["output"] += output_tokens
            self.session_cost += cost

            logger.info(f" Claude generated response ({len(response_text)} chars)")
            logger.info(f"= Cost: ${cost:.4f} (Input: {input_tokens:,}, Output: {output_tokens:,})")

            # Parse JSON response
            try:
                # Try to find JSON in response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    parsed_data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")

                logger.info(f" Parsed {len(parsed_data.get('topic_recommendations', []))} topic recommendations")

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"  Failed to parse JSON response: {e}")
                logger.info("Attempting to extract data from plain text response...")

                # Fallback: create a basic structure with the text response
                parsed_data = {
                    "topic_recommendations": [],
                    "trending_themes": [],
                    "competitor_insights": "See raw response",
                    "timing_recommendations": "See raw response",
                    "risk_warnings": [],
                    "raw_response": response_text
                }

            # Post-process with competitor title generator
            if 'topic_recommendations' in parsed_data:
                youtube_raw = research_data.get('youtube_raw', {})
                # Even if empty, we might want to run it for fallback/original tagging
                try:
                    logger.info("  Generating competitor-based title variations...")
                    for topic in parsed_data['topic_recommendations']:
                        variations = self.title_generator.generate_from_competitors(
                            topic_data=topic,
                            competitor_analysis=youtube_raw,
                            count=3
                        )
                        topic['title_variations'] = variations
                        topic['original_title'] = topic.get('title')
                        
                        # Use best variation as main title if high confidence
                        if variations and "HIGH" in variations[0].get('confidence', ''):
                            topic['title'] = variations[0]['title']
                except Exception as e:
                    logger.warning(f"  Failed to generate title variations: {e}")

            # Build final result
            parsed_data_result = parsed_data # specific variable to avoid confusion
            result = {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "model_used": self.model,
                "tokens_used": {
                    "input": input_tokens,
                    "output": output_tokens
                },
                "cost_estimate": cost,
                "topic_recommendations": parsed_data.get("topic_recommendations", []),
                "trending_themes": parsed_data.get("trending_themes", []),
                "competitor_insights": parsed_data.get("competitor_insights", ""),
                "timing_recommendations": parsed_data.get("timing_recommendations", ""),
                "risk_warnings": parsed_data.get("risk_warnings", [])
            }

            # Include raw response if parsing failed
            if "raw_response" in parsed_data:
                result["raw_response"] = parsed_data["raw_response"]

            return result

        except Exception as e:
            logger.error(f"L Claude API error: {e}")
            raise

    def format_for_email(self, data: Dict) -> str:
        """
        Format topic recommendations as beautiful HTML email.

        Args:
            data: Topic generation results from generate_topics()

        Returns:
            HTML-formatted email content
        """
        topics = data.get("topic_recommendations", [])
        themes = data.get("trending_themes", [])
        competitor = data.get("competitor_insights", "")
        timing = data.get("timing_recommendations", "")
        warnings = data.get("risk_warnings", [])

        # Build HTML email
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .summary {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-left: 4px solid #667eea; }}
        .urgent {{ background: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        .urgent h3 {{ color: #856404; margin-top: 0; }}
        .topic {{ background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 15px 0; }}
        .topic-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .topic-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin: 0; }}
        .badge {{ padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge-urgent {{ background: #dc3545; color: white; }}
        .badge-high {{ background: #28a745; color: white; }}
        .badge-medium {{ background: #ffc107; color: #000; }}
        .badge-low {{ background: #6c757d; color: white; }}
        .badge-trending {{ background: #007bff; color: white; }}
        .badge-evergreen {{ background: #17a2b8; color: white; }}
        .topic-meta {{ color: #6c757d; font-size: 14px; margin: 10px 0; }}
        .hook {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 10px 0; font-style: italic; }}
        .key-points {{ margin: 10px 0; }}
        .key-points li {{ margin: 5px 0; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .themes {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }}
        .theme-tag {{ background: #e7f3ff; color: #004085; padding: 8px 15px; border-radius: 20px; font-size: 14px; }}
        .warning {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; }}
        .footer {{ text-align: center; color: #6c757d; padding: 20px; font-size: 14px; margin-top: 40px; border-top: 1px solid #dee2e6; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>= YouTube Topic Recommendations</h1>
        <p>Generated: {data.get('timestamp', 'N/A')} | Model: {data.get('model_used', 'N/A')}</p>
        <p>Cost: ${data.get('cost_estimate', 0):.4f} | Tokens: {data.get('tokens_used', {}).get('input', 0):,} in / {data.get('tokens_used', {}).get('output', 0):,} out</p>
    </div>

    <div class="summary">
        <h3>= Executive Summary</h3>
        <p><strong>{len(topics)} video topics</strong> generated based on analysis of Google Trends, Twitter, Reddit, YouTube competitors, and breaking news from the past 24 hours.</p>
        <p><strong>Key Focus:</strong> {', '.join(themes[:3]) if themes else 'Analysis of trending topics and viral content opportunities'}</p>
    </div>
"""

        # Top 3 urgent topics
        urgent_topics = [t for t in topics if t.get('publishing_priority', 0) >= 8][:3]
        if urgent_topics:
            html += """
    <div class="urgent">
        <h3>=% URGENT: Top Priority Topics (Publish Within 24h)</h3>
"""
            for topic in urgent_topics:
                html += f"""
        <p><strong>{topic.get('rank', '?')}. {topic.get('title', 'Untitled')}</strong><br>
        Priority: {topic.get('publishing_priority', 0)}/10 | {topic.get('viral_potential', 'Unknown')}</p>
"""
            html += """
    </div>
"""

        # All topics
        html += """
    <div class="section">
        <h2>< All Topic Recommendations</h2>
"""

        for topic in topics:
            priority = topic.get('publishing_priority', 0)
            viral = topic.get('viral_potential', '')
            video_type = topic.get('video_type', '')

            # Determine badges
            priority_badge = 'badge-urgent' if priority >= 8 else 'badge-high' if priority >= 6 else 'badge-medium' if priority >= 4 else 'badge-low'
            viral_badge = 'badge-high' if 'HIGH' in viral.upper() else 'badge-medium' if 'MEDIUM' in viral.upper() else 'badge-low'
            type_badge = 'badge-trending' if 'breaking' in video_type.lower() or 'trending' in video_type.lower() else 'badge-evergreen'

            html += f"""
        <div class="topic">
            <div class="topic-header">
                <h3 class="topic-title">{topic.get('rank', '?')}. {topic.get('title', 'Untitled')}</h3>
                <div>
                    <span class="badge {priority_badge}">Priority {priority}/10</span>
                    <span class="badge {type_badge}">{video_type}</span>
                </div>
            </div>

            <div class="topic-meta">
                <strong>Duration:</strong> {topic.get('target_duration', 'N/A')} |
                <strong>Viral Potential:</strong> <span class="badge {viral_badge}">{viral}</span>
            </div>

            <div class="hook">
                <strong>< Hook (First 30 seconds):</strong><br>
                {topic.get('hook', 'N/A')}
            </div>

            <div class="key-points">
                <strong>= Key Points:</strong>
                <ul>
"""
            for point in topic.get('key_points', []):
                html += f"                    <li>{point}</li>\n"

            html += f"""
                </ul>
            </div>

            <p><strong>< Thumbnail:</strong> {topic.get('thumbnail_concept', 'N/A')}</p>
"""
            
            # evidence_sources can be list of strings or dicts
            sources = topic.get('evidence_sources', ['No sources'])
            source_names = []
            for s in sources:
                if isinstance(s, dict):
                    source_names.append(s.get('name', 'Unknown'))
                else:
                    source_names.append(str(s))
                    
            html += f"<p><strong>= Evidence Sources:</strong> {', '.join(source_names)}</p>\n"
            html += f"<p><strong>= SEO Keywords:</strong> {', '.join(topic.get('search_keywords', ['No keywords']))}</p>\n"
            html += "        </div>\n"

            html += """
    </div>
"""

        # Trending themes
        if themes:
            html += """
    <div class="section">
        <h2>= Trending Themes</h2>
        <div class="themes">
"""
            for theme in themes:
                html += f"""            <span class="theme-tag">{theme}</span>\n"""

            html += """
        </div>
    </div>
"""

        # Competitor insights
        if competitor:
            html += f"""
    <div class="section">
        <h2>< Competitor Insights</h2>
        <p>{competitor}</p>
    </div>
"""

        # Timing recommendations
        if timing:
            html += f"""
    <div class="section">
        <h2> Timing Recommendations</h2>
        <p>{timing}</p>
    </div>
"""

        # Risk warnings
        if warnings:
            html += """
    <div class="section">
        <h2> Risk Warnings</h2>
"""
            for warning in warnings:
                html += f"""        <div class="warning">{warning}</div>\n"""

            html += """
    </div>
"""

        # Footer
        html += """
    <div class="footer">
        <p>Generated by Royal Research Automation ></p>
        <p>Powered by Claude AI (Anthropic)</p>
    </div>
</body>
</html>
"""

        return html

    def get_session_stats(self) -> Dict:
        """
        Get cumulative statistics for this session.

        Returns:
            Dictionary with session token usage and cost
        """
        return {
            "total_tokens": {
                "input": self.session_tokens["input"],
                "output": self.session_tokens["output"],
                "total": self.session_tokens["input"] + self.session_tokens["output"]
            },
            "total_cost": self.session_cost
        }


# Testing block
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config

    print("="*70)
    print("> TESTING CLAUDE TOPIC GENERATOR")
    print("="*70)

    # Mock research data for testing
    mock_research_data = {
        "google_trends": """
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=
 GOOGLE TRENDS - BREAKOUT QUERIES
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
" 'Meghan Markle' - Interest: +200% (Breakout)
" 'Prince Harry update' - Interest: +150% (Rising)
" 'Royal Family news' - Interest: Steady
        """,
        "twitter": """
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=& TWITTER - VIRAL TWEETS
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=% MEGA VIRAL (15,234 engagement)
"Meghan Markle's Netflix deal reportedly in trouble after poor viewership"
        """,
        "reddit": """
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=4 REDDIT - TOP DISCUSSIONS
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
Timeline: "Meghan's project timeline shows pattern of failures" (450 upvotes, 89 comments)
        """,
        "youtube": """
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
= YOUTUBE COMPETITOR ANALYSIS
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
Jessica Talks Tea: "Meghan EXPOSED" - 5,200 VPH (VIRAL)
Competitor using split-screen thumbnails with RED badges
        """,
        "news": """
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
= NEWS ARTICLES
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
=% Daily Mail (3h old): "Meghan Markle's Netflix deal under scrutiny"
Relevance: 9.2/10
        """
    }

    print("\n Mock research data prepared")
    print(f"= Data sources: {len(mock_research_data)}")

    # Initialize generator
    generator = ClaudeTopicGenerator(
        api_key=config.ANTHROPIC_API_KEY,
        model="claude-3-5-haiku-20241022"
    )

    print("\n Generating topics from mock data...")
    print("(This will make a real API call to Claude)")

    try:
        result = generator.generate_topics(mock_research_data)

        print("\n" + "="*70)
        print("= GENERATION RESULTS")
        print("="*70)
        print(f"Topics generated: {len(result['topic_recommendations'])}")
        print(f"Tokens used: {result['tokens_used']['input']:,} in / {result['tokens_used']['output']:,} out")
        print(f"Cost: ${result['cost_estimate']:.4f}")

        if result['topic_recommendations']:
            print("\n" + "="*70)
            print("< TOP 3 TOPICS")
            print("="*70)
            for i, topic in enumerate(result['topic_recommendations'][:3], 1):
                print(f"\n{i}. {topic.get('title', 'Untitled')}")
                print(f"   Type: {topic.get('video_type', 'N/A')}")
                print(f"   Viral Potential: {topic.get('viral_potential', 'N/A')}")
                print(f"   Priority: {topic.get('publishing_priority', 0)}/10")
                print(f"   Hook: {topic.get('hook', 'N/A')[:100]}...")

        if result.get('trending_themes'):
            print("\n" + "="*70)
            print("= TRENDING THEMES")
            print("="*70)
            for theme in result['trending_themes']:
                print(f"   • {theme}")

        # Test email formatting
        print("\n" + "="*70)
        print("= TESTING EMAIL FORMATTING")
        print("="*70)
        html_email = generator.format_for_email(result)
        print(f" Generated HTML email ({len(html_email):,} characters)")
        print(f"First 200 chars: {html_email[:200]}...")

        # Session stats
        stats = generator.get_session_stats()
        print("\n" + "="*70)
        print("= SESSION STATISTICS")
        print("="*70)
        print(f"Total tokens: {stats['total_tokens']['total']:,}")
        print(f"Total cost: ${stats['total_cost']:.4f}")

        print("\n" + "="*70)
        print(" CLAUDE INTEGRATION TEST COMPLETE")
        print("="*70)
        print("\nUSAGE IN YOUR APPLICATION:")
        print("-" * 70)
        print("from generators.claude_client import ClaudeTopicGenerator")
        print("from config import ANTHROPIC_API_KEY")
        print("")
        print("generator = ClaudeTopicGenerator(ANTHROPIC_API_KEY)")
        print("result = generator.generate_topics(research_data)")
        print("html_email = generator.format_for_email(result)")

    except Exception as e:
        print(f"\nL Error during test: {e}")
        import traceback
        traceback.print_exc()
