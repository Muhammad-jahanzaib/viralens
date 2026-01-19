"""
Generate titles based on competitor analysis
Uses ACTUAL viral patterns from competitors
"""

from typing import Dict, List
import re
import random

class CompetitorTitleGenerator:
    """Generate titles matching successful competitor patterns"""
    
    def __init__(self):
        self.emotional_triggers = [
            'SHOCKING', 'UNBELIEVABLE', 'REVEALED', 'EXPOSED', 'FINALLY',
            'SECRET', 'HEARTBREAKING', 'URGENT', 'MYSTERY', 'TRAGEDY',
            'TRUTH', 'HIDDEN', 'CONFIRMED', 'INSANE', 'EMOTIONAL'
        ]
        
        self.power_prefixes = [
            "It's over:", "Just in:", "Breaking:", "Finally:", "The Truth:", 
            "Watch now:", "Wait for it:", "Total Disaster:", "Big Mistake:"
        ]
        
        self.patterns = [
            "How {PERSON} {ACTION} {TOPIC}",
            "Top {NUMBER} {TOPIC} You Need to Know",
            "{TOPIC}: What {PERSON} Won't Tell You",
            "{PERSON} {ACTION} {TOPIC_ALT} - {CONSEQUENCE}",
            "The {TOPIC} {PERSON} Tried to Hide",
            "Why {PERSON} is {ACTION} {TOPIC}",
            "{NUMBER} Times {PERSON} {ACTION} {TOPIC}",
            "{PERSON} vs {PERSON_ALT}: The {TOPIC} Showdown",
            "Is {PERSON} {ACTION} {TOPIC}?",
            "What {PERSON} Actually Thinks of {TOPIC}",
            "{ACTION}: {PERSON} and the {TOPIC} Scandal",
            "{PERSON}'s {TOPIC} - {EMOTIONAL}",
            "Beyond the Palace: {PERSON} and {TOPIC}",
            "{PERSON} {ACTION} {TOPIC}: {EMOTIONAL} Details",
            "The {EMOTIONAL} Moment {PERSON} {ACTION} {TOPIC}",
            "Inside the {TOPIC}: {PERSON} Speaks Out",
            "What Happened to {PERSON}? {TOPIC} {ACTION}",
            "{NUMBER} Facts About {PERSON} and {TOPIC}",
            "{PERSON} and {PERSON_ALT} {ACTION} {TOPIC}",
            "The Real Reason {PERSON} {ACTION} {TOPIC}",
            "{TOPIC} {ACTION} - {PERSON}'s {EMOTIONAL} Response",
            "Exclusive: {PERSON} {ACTION} {TOPIC} {CONSEQUENCE}",
            "Everything Changes: {PERSON} {ACTION} {TOPIC}",
            "Wait... {PERSON} {ACTION} {TOPIC}?",
            "Can't Believe {PERSON} {ACTION} {TOPIC}"
        ]
    
    def generate_from_competitors(
        self, 
        topic_data: Dict, 
        competitor_analysis: Dict,
        count: int = 3
    ) -> List[Dict]:
        """
        Generate title variations based on competitor viral patterns
        
        Args:
            topic_data: Your topic information (title, keywords, etc.)
            competitor_analysis: Analysis from YouTube collector
            count: Number of variations to generate
            
        Returns:
            List of title variations with competitor evidence
        """
        
        # Get viral formulas
        viral_formulas = competitor_analysis.get('viral_patterns', {}).get('viral_formulas', [])
        
        if not viral_formulas:
            return self._fallback_generation(topic_data, count)
        
        # Get top performing patterns (Pattern Extraction & Title Analysis)
        performance_data = competitor_analysis.get('viral_patterns', {}).get('performance_analysis', {})
        best_patterns = self._get_top_patterns(performance_data, count)
        
        # Extract patterns and topic entities using regex
        entities = self._extract_patterns_and_entities(topic_data)
        
        # Generate variations
        variations = []
        
        for i, pattern_type in enumerate(best_patterns[:count]):
            # Find viral formulas matching this pattern
            matching_formulas = [
                f for f in viral_formulas 
                if f.get('pattern_type') == pattern_type
            ]
            
            if not matching_formulas:
                continue
            
            # Pick top performing formula
            formula = max(matching_formulas, key=lambda f: f.get('vph', 0))
            
            # Generate title using this formula
            generated_title = self._apply_formula(formula['formula'], entities, topic_data)
            
            # Calculate confidence based on competitor performance
            avg_vph = formula.get('vph', 0)
            confidence_level = self._calculate_confidence(avg_vph)
            
            variation = {
                'title': generated_title,
                'pattern_type': pattern_type,
                'based_on': {
                    'competitor_channel': formula.get('channel', ''),
                    'original_title': formula.get('original_title', ''),
                    'performance': f"{formula.get('views', 0):,} views, {formula.get('vph', 0):,.0f} VPH",
                    'published': f"{formula.get('published', 0):.0f} hours ago"
                },
                'confidence': confidence_level,
                'reasoning': self._explain_formula_choice(formula, pattern_type, avg_vph),
                'why_this_works': self._explain_pattern_success(pattern_type, performance_data)
            }
            
            variations.append(variation)
        
        return variations
    
    def _get_top_patterns(self, performance_data: Dict, count: int) -> List[str]:
        """Get top performing pattern types"""
        
        by_pattern = performance_data.get('by_pattern', {})
        
        # Sort by average VPH
        sorted_patterns = sorted(
            by_pattern.items(),
            key=lambda x: x[1].get('avg_vph', 0),
            reverse=True
        )
        
        return [pattern[0] for pattern in sorted_patterns[:count]]
    
    def _extract_patterns_and_entities(self, topic_data: Dict) -> Dict:
        """Extract patterns and key entities from topic using regex"""
        
        title = topic_data.get('title', '')
        keywords = topic_data.get('search_keywords', [])
        
        # Extract person names (simple heuristic - can be improved)
        person_candidates = []
        for keyword in keywords:
            if any(name in keyword for name in ['Meghan', 'Harry', 'Kate', 'William', 'Charles']):
                person_candidates.append(keyword)
        
        # Extract topics/subjects
        topics = [kw for kw in keywords if kw not in person_candidates]
        
        return {
            'person': person_candidates[0] if person_candidates else 'Royal Family',
            'person_alt': person_candidates[1] if len(person_candidates) > 1 else None,
            'topic': topics[0] if topics else 'Latest News',
            'topic_alt': topics[1] if len(topics) > 1 else None,
            'action': self._extract_action(title),
            'consequence': self._extract_consequence(title)
        }
    
    def _extract_action(self, title: str) -> str:
        """Extract action verb from title"""
        
        actions = ['EXPOSED', 'REVEALS', 'ANNOUNCES', 'CONFIRMS', 'BREAKS', 
                  'DROPS', 'RELEASES', 'FIRES BACK', 'RESPONDS', 'SLAMS',
                  'IGNORES', 'ATTACKS', 'DEFENDS', 'ADMITS', 'DENIES']
        
        for action in actions:
            if action in title.upper():
                return action
        
        return random.choice(['REVEALS', 'SPEAKS OUT', 'BREAKS SILENCE'])
    
    def _extract_consequence(self, title: str) -> str:
        """Extract consequence/outcome from title"""
        
        if ':' in title:
            parts = title.split(':')
            if len(parts) > 1:
                return parts[1].strip()
        
        return 'What Happens Next'
    
    def _apply_formula(self, formula: str, entities: Dict, topic_data: Dict) -> str:
        """Apply formula with actual entities"""
        
        title = formula
        
        # Replace placeholders
        replacements = {
            '{PERSON}': entities.get('person', 'Meghan Markle'),
            '{PERSON_ALT}': entities.get('person_alt', 'Prince Harry'),
            '{TOPIC}': entities.get('topic', 'Royal Drama'),
            '{TOPIC_ALT}': entities.get('topic_alt', 'Palace News'),
            '{ACTION}': entities.get('action', 'REVEALS'),
            '{CONSEQUENCE}': entities.get('consequence', 'Everything Changes'),
            '{EMOTIONAL}': random.choice(self.emotional_triggers),
            '{NUMBER}': str(random.choice([3, 5, 7, 9, 11, 13]))
        }
        
        for placeholder, value in replacements.items():
            if value:
                title = title.replace(placeholder, value)
        
        # Clean up any remaining placeholders
        title = re.sub(r'\{[^}]+\}', '', title)
        
        # Ensure title length is optimal (50-70 chars)
        if len(title) > 70:
            title = self._shorten_title(title)
        elif len(title) < 50:
            title = self._lengthen_title(title, topic_data)
        
        return title.strip()
    
    def _shorten_title(self, title: str) -> str:
        """Shorten title while keeping core message"""
        
        # Remove filler words
        fillers = [' the ', ' a ', ' an ', ' of ', ' for ', ' to ']
        for filler in fillers:
            title = title.replace(filler, ' ')
        
        # If still too long, truncate after colon/hyphen
        if len(title) > 70:
            if ':' in title:
                parts = title.split(':')
                title = parts[0].strip()
            elif ' - ' in title:
                parts = title.split(' - ')
                title = parts[0].strip()
        
        return title
    
    def _lengthen_title(self, title: str, topic_data: Dict) -> str:
        """Add context to short title"""
        
        # Add power words if missing
        if len(title) < 60:
            if random.random() > 0.5:
                # Prefix
                title = f"{random.choice(self.power_prefixes)} {title}"
            else:
                # Suffix
                power_additions = [
                    ' - The SHOCKING Truth',
                    ' (What Really Happened)',
                    ': Everything We Know',
                    ' - Body Language REVEALS All',
                    ' | Breaking News',
                    ' [READ NOW]',
                    ' (EMOTIONAL)'
                ]
                title += random.choice(power_additions)
        
        return title
    
    def _calculate_confidence(self, avg_vph: float) -> str:
        """Calculate confidence level based on competitor performance"""
        
        if avg_vph > 5000:
            return "🔥 VERY HIGH (Proven viral pattern)"
        elif avg_vph > 2000:
            return "✅ HIGH (Strong performer)"
        elif avg_vph > 1000:
            return "📈 GOOD (Solid choice)"
        else:
            return "⚠️ MODERATE (Test carefully)"
    
    def _explain_formula_choice(self, formula: Dict, pattern_type: str, avg_vph: float) -> str:
        """Explain why this formula was chosen"""
        
        channel = formula.get('channel', 'a top competitor')
        views = formula.get('views', 0)
        
        return (
            f"Based on {channel}'s video that got {views:,} views. "
            f"This {pattern_type} pattern averages {avg_vph:,.0f} views/hour. "
            f"Original title: \"{formula.get('original_title', '')}\""
        )
    
    def _explain_pattern_success(self, pattern_type: str, performance_data: Dict) -> str:
        """Explain why this pattern works"""
        
        explanations = {
            'REVELATION': "Revelation titles create curiosity gaps - viewers want to know the 'exposed' secret. Strong emotional trigger.",
            'BREAKING_NEWS': "Breaking news creates urgency - FOMO (fear of missing out) drives clicks. Time-sensitive value.",
            'QUESTION': "Questions engage viewers directly - they want to find the answer. Creates active participation.",
            'COMPARISON': "Comparisons create drama and controversy - viewers pick sides. High engagement potential.",
            'TRUTH_SEEKING': "Truth-seeking satisfies need to know 'real story' - positions you as insider. Builds authority.",
            'ANALYSIS': "Analysis attracts educated audience - shows depth. Good for retention and credibility.",
            'NUMBERED_LIST': "Lists promise clear structure - easy to consume. High CTR due to specificity.",
            'OTHER': "Proven pattern from competitor analysis - mirrors successful formula."
        }
        
        base_explanation = explanations.get(pattern_type, explanations['OTHER'])
        
        # Add performance context
        pattern_data = performance_data.get('by_pattern', {}).get(pattern_type, {})
        count = pattern_data.get('count', 0)
        avg_vph = pattern_data.get('avg_vph', 0)
        
        if count > 0:
            base_explanation += f" Your competitors used this {count} times with avg {avg_vph:,.0f} VPH."
        
        return base_explanation
    
    def _fallback_generation(self, topic_data: Dict, count: int) -> List[Dict]:
        """Fallback if no competitor data available"""
        
        base_title = topic_data.get('title', '')
        
        return [{
            'title': base_title,
            'pattern_type': 'ORIGINAL',
            'based_on': {
                'competitor_channel': 'N/A',
                'original_title': 'No competitor data available',
                'performance': 'N/A',
                'published': 'N/A'
            },
            'confidence': '⚠️ LOW (No competitor data)',
            'reasoning': 'No competitor videos found in the past 48 hours. Using original topic title.',
            'why_this_works': 'Add competitors to settings for AI-powered title optimization based on viral patterns.'
        }]
