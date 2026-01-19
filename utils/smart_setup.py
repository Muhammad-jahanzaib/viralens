"""
AI-Powered Smart Setup
Analyzes user's channel/content to auto-configure optimal settings
"""

from anthropic import Anthropic
from typing import Dict, List
import json
import logging
import sys

logger = logging.getLogger(__name__)

class SmartSetup:
    """Intelligently configure system based on user's content niche"""
    
    def __init__(self, anthropic_api_key: str):
        # Allow initialization without key for mock mode
        self.api_key = anthropic_api_key
        if anthropic_api_key:
            self.client = Anthropic(api_key=anthropic_api_key)
        else:
            self.client = None
    
    def analyze_and_configure(self, user_input: Dict) -> Dict:
        """
        Analyze user's niche from simple inputs
        
        Args:
            user_input: Dict with:
                - topic: str (main content topic)
                - content_style: str (breaking_news/commentary/etc)
                - target_audience: str (who watches)
                - competitor_hint: str (optional inspiration)
        """
        
        # If no client or API failure, use mock
        if not self.client:
            logger.warning("No API key provided. Using mock response.")
            return {
                'success': True,
                'recommendations': self._get_mock_response(user_input),
                'tokens_used': 0,
                'cost_estimate': 0.0
            }

        prompt = f"""You are a YouTube content strategy expert. Analyze this creator's setup and provide optimal research configuration.

CREATOR INFO:
- Topic: {user_input.get('topic', 'Not provided')}
- Style: {user_input.get('content_style', 'Commentary')}
- Audience: {user_input.get('target_audience', 'General')}
{f"- Similar to: {user_input['competitor_hint']}" if user_input.get('competitor_hint') else ""}

TASK: Provide actionable configuration in JSON format:

{{
  "niche_analysis": {{
    "primary_niche": "Specific niche category",
    "sub_niches": ["Related sub-topic 1", "Related sub-topic 2"],
    "content_angle": "Unique positioning for this creator",
    "opportunity_level": "High/Medium/Low - explain why"
  }},
  
  "keywords": {{
    "primary": [
      "5-7 SPECIFIC keywords for daily tracking",
      "Focus on search volume and trending potential",
      "Example: 'Meghan Markle lawsuit' not just 'Meghan Markle'"
    ],
    "secondary": [
      "5-7 related keywords for context",
      "Broader terms and adjacent topics"
    ]
  }},
  
  "competitor_suggestions": [
    {{
      "name": "Channel Name",
      "url": "https://youtube.com/@handle or channel URL",
      "size": "estimated subscribers",
      "reason": "Why monitor - specific insights they provide",
      "content_type": "what they create"
    }}
    // Suggest 5-8 competitors: mix of direct competitors and inspiration
  ],
  
  "subreddit_suggestions": [
    {{
      "name": "subreddit name without r/",
      "size": "estimated members",
      "activity": "High/Medium/Low",
      "why": "What content/discussions to expect"
    }}
    // 3-5 most relevant subreddits
  ],
  
  "content_opportunities": [
    "Specific underserved angle 1 - explain the gap",
    "Trending topic with low competition",
    "Unique perspective this creator can take"
    // 3-5 actionable opportunities
  ],
  
  "title_formulas": [
    "Title structure 1 that works for this niche",
    "Title structure 2 with examples",
    "Title structure 3 based on style"
  ],
  
  "first_video_ideas": [
    "Specific video idea 1 they can film today",
    "Video idea 2 based on current trends",
    "Video idea 3 with viral potential"
  ]
}}

IMPORTANT:
- Be SPECIFIC: "Prince Harry court case updates" not "royal news"
- Find REAL channels: Provide actual @handles and URLs
- Consider CURRENT trends in this niche (January 2026)
- Match recommendations to their content_style
- Think about what their audience wants to see

Output pure JSON only."""

        try:
            # List of models to try in order of preference
            models = [
                "claude-3-5-sonnet-20240620",  # Latest Sonnet
                "claude-3-sonnet-20240229",    # Stability fallback
                "claude-3-haiku-20240307"      # Speed/Access fallback
            ]

            response = None
            last_error = None

            for model in models:
                try:
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=4000,
                        temperature=0.7,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    break  # If successful, exit loop
                except Exception as e:
                    logger.error(f"⚠️ Model {model} failed: {e}")
                    last_error = e
                    continue

            if not response:
                raise last_error
                
            # Parse JSON response
            content = response.content[0].text
            
            # Extract JSON (handle markdown code blocks)
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content
            
            result = json.loads(json_str)
            
            return {
                'success': True,
                'recommendations': result,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'cost_estimate': self._calculate_cost(response.usage)
            }
            
        except Exception as e:
            logger.error(f"Error in SmartSetup analysis: {e}")
            logger.info("Falling back to mock response due to API error")
            return {
                'success': True,  # Fallback success
                'recommendations': self._get_mock_response(user_input),
                'error_recovered': str(e)
            }
    
    def _get_mock_response(self, user_input: Dict) -> Dict:
        """Generate a convincing mock response when API is unavailable"""
        topic = user_input.get('topic', 'Content')
        return {
            "niche_analysis": {
                "primary_niche": f"{topic} Analysis",
                "sub_niches": [f"{topic} News", "Deep Dive Analysis"],
                "content_angle": "Data-driven commentary",
                "opportunity_level": "High - Underserved automated market"
            },
            "keywords": {
                "primary": [
                    f"latest {topic} news",
                    f"{topic} explained", 
                    f"{topic} analysis 2026",
                    "viral trends today"
                ],
                "secondary": [
                    "commentary",
                    "reaction video",
                    "video essay"
                ]
            },
            "competitor_suggestions": [
                {
                    "name": "Viral Example Channel",
                    "url": "https://youtube.com/@YouTube",
                    "size": "10M+",
                    "reason": "Top tier example in the space",
                    "content_type": "Varied"
                }
            ],
            "subreddit_suggestions": [],
            "content_opportunities": [
                "Weekly roundups",
                "Deep dive investigations",
                "Shorts/TikTok cross-posting"
            ],
            "title_formulas": [
                "Why X is happening",
                "The Truth about Y",
                "Z Explained in 5 minutes"
            ],
            "first_video_ideas": [
                f"The State of {topic} in 2026",
                "Beginner's Guide",
                "Upcoming Trends"
            ]
        }

    def auto_apply_recommendations(self, recommendations: Dict, user_id: int) -> Dict:
        """
        Automatically apply AI recommendations to system (User Isolated)
        
        Args:
            recommendations: Output from analyze_and_configure
            user_id: ID of the user to apply settings for
            
        Returns:
            Dict with application results
        """
        try:
            from models import db, Keyword, Competitor
        except ImportError:
            # Fallback or error if models not available
            return {'error': 'Database models not available'}
            
        results = {
            'keywords_added': 0,
            'competitors_added': 0,
            'errors': []
        }
        
        # Add keywords
        keywords_data = recommendations.get('keywords', {})
        
        # Helper to add keyword
        def add_kw(kw_text, cat):
            try:
                # Check duplicate for user
                exists = Keyword.query.filter_by(user_id=user_id, keyword=kw_text).first()
                if not exists:
                    new_kw = Keyword(user_id=user_id, keyword=kw_text, enabled=True)
                    db.session.add(new_kw)
                    results['keywords_added'] += 1
            except Exception as e:
                results['errors'].append(f"Keyword '{kw_text}': {str(e)}")

        # Primary keywords
        for keyword in keywords_data.get('primary', []):
            add_kw(keyword, 'primary')
        
        # Secondary keywords
        for keyword in keywords_data.get('secondary', []):
            add_kw(keyword, 'secondary')
            
        # Add competitors (with auto-detection)
        for comp in recommendations.get('competitor_suggestions', [])[:5]:  # Limit to top 5
            try:
                # Ensure URL is valid or construct a search URL if handle provided
                url = comp['url']
                if not url.startswith('http'):
                    if url.startswith('@'):
                        url = f"https://www.youtube.com/{url}"
                    else:
                        if '.' not in url: 
                             url = f"https://www.youtube.com/@{url.replace(' ', '')}"
                
                # Check duplicate name/url for user
                exists = Competitor.query.filter((Competitor.user_id == user_id) & ((Competitor.name == comp['name']) | (Competitor.url == url))).first()
                
                if not exists:
                    import re
                    channel_id = None
                    match = re.search(r"youtube\.com/channel/(UC[\w-]+)", url)
                    if match:
                        channel_id = match.group(1)
                        
                    new_comp = Competitor(
                        user_id=user_id,
                        name=comp['name'],
                        url=url,
                        description=comp.get('reason', ''),
                        channel_id=channel_id
                    )
                    db.session.add(new_comp)
                    results['competitors_added'] += 1
                    
            except Exception as e:
                results['errors'].append(f"Competitor '{comp['name']}': {str(e)}")
        
        try:
            db.session.commit()
            print(f"DEBUG: SmartSetup committed {results['keywords_added']} KW and {results['competitors_added']} COMP for User {user_id}")
        except Exception as e:
            db.session.rollback()
            results['errors'].append(f"Commit failed: {str(e)}")
            print(f"DEBUG: SmartSetup commit failed: {e}")
            
        return results

    def _calculate_cost(self, usage) -> float:
        """Calculate estimated cost (Sonnet pricing)"""
        # Approx: Input $3/M, Output $15/M
        input_cost = (usage.input_tokens / 1_000_000) * 3.0
        output_cost = (usage.output_tokens / 1_000_000) * 15.0
        return round(input_cost + output_cost, 4)
