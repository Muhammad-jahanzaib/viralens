"""
Explain WHY a topic was prioritized
Builds trust through transparency
"""

from typing import Dict, List
from datetime import datetime

class TopicExplainer:
    """Generates human-readable explanations for topic rankings"""
    
    def explain_ranking(self, topic: Dict, all_topics: List[Dict]) -> Dict:
        """
        Generate detailed explanation of why this topic ranked where it did
        
        Returns:
            Dict with explanation components
        """
        
        # Normalize evidence sources if they are strings
        if 'evidence_sources' in topic:
            normalized_sources = []
            for s in topic['evidence_sources']:
                if isinstance(s, dict):
                    normalized_sources.append(s)
                else:
                    # Heuristic parsing for strings
                    s_str = str(s).lower()
                    platform = 'News' # Default
                    if 'twitter' in s_str or 'x.com' in s_str: platform = 'Twitter'
                    elif 'reddit' in s_str: platform = 'Reddit'
                    elif 'youtube' in s_str: platform = 'YouTube'
                    
                    normalized_sources.append({
                        'platform': platform,
                        'name': str(s),
                        'hours_ago': 12, # Safe default
                        'verified': True,
                        'likes': 1000,
                        'views': 5000
                    })
            topic['evidence_sources'] = normalized_sources

        # Normalize competitor videos if they are strings
        if 'competitor_videos' in topic:
            normalized_comps = []
            for c in topic['competitor_videos']:
                if isinstance(c, dict):
                    normalized_comps.append(c)
                else:
                    normalized_comps.append({'title': str(c)})
            topic['competitor_videos'] = normalized_comps

        explanation = {
            'overall_score': topic.get('publishing_priority', 5),
            'rank': topic.get('rank', 0),
            'total_topics': len(all_topics),
            'percentile': self._calculate_percentile(topic, all_topics),
            
            # Score components
            'components': {
                'recency': self._explain_recency(topic),
                'engagement': self._explain_engagement(topic),
                'evidence_quality': self._explain_evidence(topic),
                'trend_momentum': self._explain_trends(topic),
                'competition_gap': self._explain_competition(topic)
            },
            
            # Comparative analysis
            'strengths': self._identify_strengths(topic),
            'weaknesses': self._identify_weaknesses(topic),
            'why_beat_others': self._compare_to_others(topic, all_topics),
            
            # Action guidance
            'timing_recommendation': self._timing_advice(topic),
            'optimization_tips': self._optimization_suggestions(topic),
            'risk_factors': self._identify_risks(topic)
        }
        
        return explanation
    
    def _explain_recency(self, topic: Dict) -> Dict:
        """Explain recency score"""
        sources = topic.get('evidence_sources', [])
        
        # Find most recent source
        most_recent_hours = min([s.get('hours_ago', 99) for s in sources], default=24)
        
        if most_recent_hours < 3:
            score = 10
            explanation = f"🔥 BREAKING: Activity within {most_recent_hours:.1f} hours"
            impact = "HIGH - Strike while hot for maximum views"
        elif most_recent_hours < 12:
            score = 8
            explanation = f"⚡ FRESH: Activity within {most_recent_hours:.1f} hours"
            impact = "GOOD - Still trending, act fast"
        elif most_recent_hours < 24:
            score = 6
            explanation = f"📅 RECENT: Activity within {most_recent_hours:.1f} hours"
            impact = "MODERATE - Timely but not urgent"
        else:
            score = 4
            explanation = f"📆 OLDER: Activity {most_recent_hours:.1f} hours ago"
            impact = "LOW - Consider more recent topics first"
        
        return {
            'score': score,
            'explanation': explanation,
            'impact': impact,
            'data_point': f"{most_recent_hours:.1f} hours ago"
        }
    
    def _explain_engagement(self, topic: Dict) -> Dict:
        """Explain engagement score"""
        sources = topic.get('evidence_sources', [])
        
        total_engagement = 0
        engagement_breakdown = []
        
        for source in sources:
            if source.get('platform') == 'Twitter':
                eng = source.get('likes', 0) + source.get('retweets', 0) * 2 + source.get('replies', 0) * 3
                total_engagement += eng
                engagement_breakdown.append(f"Twitter: {eng:,} interactions")
            elif source.get('platform') == 'Reddit':
                eng = source.get('upvotes', 0) + source.get('comments', 0) * 5
                total_engagement += eng
                engagement_breakdown.append(f"Reddit: {eng:,} interactions")
            elif source.get('platform') == 'YouTube':
                eng = source.get('views', 0) / 100  # Normalize
                total_engagement += eng
                engagement_breakdown.append(f"YouTube: {source.get('views', 0):,} views")
        
        if total_engagement > 50000:
            score = 10
            level = "🔥 MEGA VIRAL"
            impact = "Proven viral potential - high confidence"
        elif total_engagement > 20000:
            score = 8
            level = "🚀 HIGH ENGAGEMENT"
            impact = "Strong interest - likely to perform well"
        elif total_engagement > 5000:
            score = 6
            level = "📈 GOOD ENGAGEMENT"
            impact = "Solid interest - moderate potential"
        else:
            score = 4
            level = "💤 LOW ENGAGEMENT"
            impact = "Limited proven interest - higher risk"
        
        return {
            'score': score,
            'level': level,
            'total': f"{total_engagement:,.0f} total interactions",
            'breakdown': engagement_breakdown,
            'impact': impact
        }
    
    def _explain_evidence(self, topic: Dict) -> Dict:
        """Explain evidence quality score"""
        sources = topic.get('evidence_sources', [])
        
        verified_count = sum(1 for s in sources if s.get('verified', False))
        platform_diversity = len(set(s.get('platform') for s in sources))
        
        if len(sources) >= 4 and platform_diversity >= 3:
            score = 10
            quality = "🏆 EXCELLENT"
            explanation = f"{len(sources)} sources across {platform_diversity} platforms"
            impact = "Well-documented from multiple angles"
        elif len(sources) >= 3:
            score = 7
            quality = "✅ GOOD"
            explanation = f"{len(sources)} sources"
            impact = "Sufficient evidence for credibility"
        elif len(sources) >= 2:
            score = 5
            quality = "⚠️ MODERATE"
            explanation = f"Only {len(sources)} sources"
            impact = "May need additional research"
        else:
            score = 3
            quality = "❌ WEAK"
            explanation = f"Only {len(sources)} source"
            impact = "High risk - insufficient evidence"
        
        return {
            'score': score,
            'quality': quality,
            'explanation': explanation,
            'source_count': len(sources),
            'verified_count': verified_count,
            'platforms': platform_diversity,
            'impact': impact
        }
    
    def _explain_trends(self, topic: Dict) -> Dict:
        """Explain trend momentum"""
        # Check if topic matches trending keywords
        keywords = topic.get('search_keywords', [])
        
        # Simulate trend data (in production, pull from Google Trends collector)
        trending_keywords = ['exposed', 'breaking', 'reveals', 'shocking']
        
        trend_matches = sum(1 for kw in keywords if any(t in kw.lower() for t in trending_keywords))
        
        if trend_matches >= 3:
            score = 9
            momentum = "📈 STRONG UPTREND"
            impact = "Riding multiple trending waves"
        elif trend_matches >= 2:
            score = 7
            momentum = "↗️ RISING"
            impact = "Catching momentum early"
        elif trend_matches >= 1:
            score = 5
            momentum = "→ STABLE"
            impact = "Steady interest"
        else:
            score = 3
            momentum = "↘️ DECLINING"
            impact = "May have peaked"
        
        return {
            'score': score,
            'momentum': momentum,
            'impact': impact,
            'trending_elements': trend_matches
        }
    
    def _explain_competition(self, topic: Dict) -> Dict:
        """Explain competition gap analysis"""
        # Check if competitors have covered this
        competitor_coverage = topic.get('competitor_videos', [])
        
        if len(competitor_coverage) == 0:
            score = 10
            gap = "🎯 BLUE OCEAN"
            explanation = "No competitors covering this yet"
            impact = "First-mover advantage - high opportunity"
        elif len(competitor_coverage) <= 2:
            score = 7
            gap = "🟢 LOW COMPETITION"
            explanation = f"Only {len(competitor_coverage)} competitor(s) covered this"
            impact = "Room for your unique angle"
        elif len(competitor_coverage) <= 5:
            score = 5
            gap = "🟡 MODERATE COMPETITION"
            explanation = f"{len(competitor_coverage)} competitors covered this"
            impact = "Need strong differentiation"
        else:
            score = 3
            gap = "🔴 HIGH COMPETITION"
            explanation = f"{len(competitor_coverage)} competitors already covered"
            impact = "Saturated - consider different angle"
        
        return {
            'score': score,
            'gap': gap,
            'explanation': explanation,
            'competitor_count': len(competitor_coverage),
            'impact': impact
        }
    
    def _identify_strengths(self, topic: Dict) -> List[str]:
        """Identify topic's main strengths"""
        strengths = []
        
        # Check various factors
        if topic.get('viral_potential') == 'HIGH':
            strengths.append("✅ High viral potential based on engagement patterns")
        
        evidence_count = len(topic.get('evidence_sources', []))
        if evidence_count >= 4:
            strengths.append(f"✅ Strong evidence base ({evidence_count} sources)")
        
        if any('breaking' in kw.lower() for kw in topic.get('search_keywords', [])):
            strengths.append("✅ Breaking news angle - time-sensitive value")
        
        if topic.get('publishing_priority', 0) >= 8:
            strengths.append("✅ Top-tier priority - highly recommended")
        
        return strengths
    
    def _identify_weaknesses(self, topic: Dict) -> List[str]:
        """Identify potential weaknesses"""
        weaknesses = []
        
        evidence_count = len(topic.get('evidence_sources', []))
        if evidence_count < 2:
            weaknesses.append("⚠️ Limited evidence - may need additional research")
        
        # Check freshness
        sources = topic.get('evidence_sources', [])
        if sources:
            oldest = max([s.get('hours_ago', 0) for s in sources], default=0)
            if oldest > 48:
                weaknesses.append(f"⚠️ Oldest source is {oldest:.0f}h old - story may be dated")
        
        if not topic.get('thumbnail_concept'):
            weaknesses.append("⚠️ No thumbnail concept provided")
        
        return weaknesses
    
    def _compare_to_others(self, topic: Dict, all_topics: List[Dict]) -> List[str]:
        """Explain why this beat lower-ranked topics"""
        comparisons = []
        
        current_rank = topic.get('rank', 0)
        current_priority = topic.get('publishing_priority', 5)
        
        # Find next lower topic
        lower_topics = [t for t in all_topics if t.get('rank', 0) > current_rank]
        
        if lower_topics:
            next_lower = min(lower_topics, key=lambda t: t.get('rank', 0))
            
            if current_priority > next_lower.get('publishing_priority', 5):
                diff = current_priority - next_lower.get('publishing_priority', 5)
                comparisons.append(f"📊 Scored {diff} points higher than #{next_lower.get('rank')}")
            
            # Compare specific factors
            current_evidence = len(topic.get('evidence_sources', []))
            lower_evidence = len(next_lower.get('evidence_sources', []))
            
            if current_evidence > lower_evidence:
                comparisons.append(f"📚 {current_evidence - lower_evidence} more evidence source(s)")
        
        return comparisons
    
    def _timing_advice(self, topic: Dict) -> Dict:
        """Provide timing recommendation"""
        most_recent_hours = min([s.get('hours_ago', 99) 
                                for s in topic.get('evidence_sources', [])], default=24)
        
        if most_recent_hours < 6:
            urgency = "🚨 URGENT"
            advice = "Publish within 4-6 hours for maximum impact"
            window = "Next 4-6 hours"
        elif most_recent_hours < 24:
            urgency = "⏰ TIMELY"
            advice = "Publish within 24 hours while still relevant"
            window = "Next 12-24 hours"
        else:
            urgency = "📅 FLEXIBLE"
            advice = "Evergreen topic - schedule at optimal posting time"
            window = "Next 48 hours"
        
        return {
            'urgency': urgency,
            'advice': advice,
            'window': window
        }
    
    def _optimization_suggestions(self, topic: Dict) -> List[str]:
        """Suggest ways to improve the topic/video"""
        suggestions = []
        
        # Check title
        title_len = len(topic.get('title', ''))
        if title_len < 50:
            suggestions.append("💡 Title is short - consider adding emotional trigger word")
        elif title_len > 80:
            suggestions.append("💡 Title is long - may get truncated, consider shortening")
        
        # Check hook
        hook = topic.get('hook', '')
        if len(hook) < 100:
            suggestions.append("💡 Hook could be stronger - add more intrigue/curiosity")
        
        # Check keywords
        keywords = topic.get('search_keywords', [])
        if len(keywords) < 5:
            suggestions.append("💡 Add more SEO keywords for better discoverability")
        
        # Evidence diversity
        platforms = set(s.get('platform') for s in topic.get('evidence_sources', []))
        if len(platforms) < 3:
            suggestions.append(f"💡 Evidence from only {len(platforms)} platform(s) - diversify sources")
        
        return suggestions
    
    def _identify_risks(self, topic: Dict) -> List[str]:
        """Identify potential risks"""
        risks = []
        
        # Check competition
        competitor_count = len(topic.get('competitor_videos', []))
        if competitor_count > 5:
            risks.append("⚠️ HIGH COMPETITION - Many competitors already covered this")
        
        # Check evidence age
        sources = topic.get('evidence_sources', [])
        if sources and max([s.get('hours_ago', 0) for s in sources], default=0) > 72:
            risks.append("⚠️ DATED - Story may be old news")
        
        # Check evidence quality
        if len(sources) < 2:
            risks.append("⚠️ THIN EVIDENCE - May be perceived as speculative")
        
        return risks
    
    def _calculate_percentile(self, topic: Dict, all_topics: List[Dict]) -> int:
        """Calculate what percentile this topic is in"""
        rank = topic.get('rank', 0)
        total = len(all_topics)
        
        if total == 0:
            return 0
        
        return int((1 - (rank - 1) / total) * 100)
