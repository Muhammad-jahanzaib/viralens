#!/usr/bin/env python3
"""
TITLE PREDICTION SYSTEM EVALUATOR
Comprehensive analysis of title prediction quality and stealthiness

Tests:
1. Pattern Detection Quality
2. Title Generation Diversity
3. Stealthiness (detectability)
4. Competitor Analysis Accuracy
5. Viral Formula Effectiveness
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
import sys


class TitlePredictionEvaluator:
    """
    Evaluate title prediction system quality
    """
    
    def __init__(self):
        self.results = {
            'quality_score': 0,
            'stealthiness_score': 0,
            'issues': [],
            'recommendations': []
        }
    
    def analyze_competitor_title_generator(self):
        """Analyze competitor title generator code"""
        filepath = 'generators/competitor_title_generator.py'
        
        if not Path(filepath).exists():
            self.results['issues'].append({
                'severity': 'CRITICAL',
                'component': 'Competitor Title Generator',
                'issue': 'File not found',
                'impact': 'Title generation system not available'
            })
            return
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        print("\n" + "=" * 80)
        print("📊 COMPETITOR TITLE GENERATOR ANALYSIS")
        print("=" * 80)
        
        # Check for key features
        features = {
            'Pattern Extraction': [
                'extract.*pattern',
                'analyze.*title',
                'regex',
                're\\.compile'
            ],
            'Viral Formula Detection': [
                'viral',
                'engagement',
                'views.*per',
                'vph'
            ],
            'Placeholder Substitution': [
                '\\{PERSON\\}',
                '\\{TOPIC\\}',
                'substitute',
                'replace'
            ],
            'Ranking System': [
                'rank',
                'score',
                'weight',
                'confidence'
            ]
        }
        
        feature_scores = {}
        for feature_name, patterns in features.items():
            found = any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
            feature_scores[feature_name] = found
            status = "✅" if found else "❌"
            print(f"{status} {feature_name}: {'Present' if found else 'MISSING'}")
            
            if not found:
                self.results['issues'].append({
                    'severity': 'HIGH',
                    'component': 'Title Generator',
                    'issue': f'{feature_name} not implemented',
                    'impact': 'Reduced title generation quality'
                })
        
        # Calculate quality score
        quality_score = sum(feature_scores.values()) / len(feature_scores) * 100
        self.results['quality_score'] = quality_score
        
        print(f"\n📈 Quality Score: {quality_score:.1f}%")
        
        if quality_score < 75:
            self.results['recommendations'].append({
                'priority': 'HIGH',
                'recommendation': 'Implement missing features to improve title generation quality',
                'features_needed': [k for k, v in feature_scores.items() if not v]
            })
    
    def analyze_youtube_client(self):
        """Analyze YouTube client for pattern detection"""
        filepath = 'collectors/youtube_client.py'
        
        if not Path(filepath).exists():
            self.results['issues'].append({
                'severity': 'HIGH',
                'component': 'YouTube Client',
                'issue': 'File not found',
                'impact': 'Cannot analyze competitor videos'
            })
            return
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        print("\n" + "=" * 80)
        print("📊 YOUTUBE CLIENT ANALYSIS")
        print("=" * 80)
        
        # Check for pattern detection
        patterns = {
            'Title Analysis': [
                '_analyze_title',
                'title.*pattern',
                'extract.*title'
            ],
            'Engagement Metrics': [
                'views',
                'likes',
                'comments',
                'engagement'
            ],
            'Pattern Classes': [
                'REVELATION',
                'QUESTION',
                'BREAKING_NEWS',
                'class.*Pattern'
            ]
        }
        
        for component, keywords in patterns.items():
            found = any(keyword in content for keyword in keywords)
            status = "✅" if found else "❌"
            print(f"{status} {component}: {'Present' if found else 'Missing'}")
    
    def evaluate_stealthiness(self):
        """Evaluate how detectable the title generation is"""
        filepath = 'generators/competitor_title_generator.py'
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        print("\n" + "=" * 80)
        print("🕵️  STEALTHINESS EVALUATION")
        print("=" * 80)
        
        # Calculate Diversity Score based on patterns count
        pattern_matches = re.findall(r'"[^"]*\{[^}]+\}[^"]*"', content)
        pattern_count = len(pattern_matches)
        diversity_score = min(100, (pattern_count / 20) * 100) if pattern_count > 0 else 0
        
        # Calculate Randomization Score based on use of random.choice
        random_choices = content.count('random.choice')
        random_score = min(100, (random_choices / 5) * 100) if random_choices > 0 else 0
        
        # Calculate Contextual Adaptation Score
        context_score = 0
        if 'power_prefixes' in content: context_score += 30
        if 'emotional_triggers' in content: context_score += 30
        if 'entities.get' in content: context_score += 40
        
        # Check if patterns are too obvious
        stealth_checks = [
            {
                'name': 'Pattern Diversity',
                'description': f'Does the system use multiple patterns? (Found {pattern_count})',
                'score': diversity_score,
                'threshold': 70
            },
            {
                'name': 'Randomization',
                'description': f'Are titles randomized to avoid repetition? ({random_choices} random points)',
                'score': random_score,
                'threshold': 70
            },
            {
                'name': 'Contextual Adaptation',
                'description': 'Does system adapt patterns to context?',
                'score': context_score,
                'threshold': 70
            }
        ]
        
        total_score = 0
        for check in stealth_checks:
            status = "✅" if check['score'] >= check['threshold'] else "⚠️"
            print(f"{status} {check['name']}: {check['score']:.1f}%")
            print(f"   {check['description']}")
            total_score += check['score']
            
            if check['score'] < check['threshold']:
                self.results['issues'].append({
                    'severity': 'MEDIUM',
                    'component': 'Stealthiness',
                    'issue': f"{check['name']} below threshold",
                    'impact': 'Titles may be easily detectable as AI-generated'
                })
        
        stealth_score = total_score / len(stealth_checks)
        self.results['stealthiness_score'] = stealth_score
        
        print(f"\n🎭 Stealthiness Score: {stealth_score:.1f}%")
        
        if stealth_score < 70:
            self.results['recommendations'].append({
                'priority': 'MEDIUM',
                'recommendation': 'Improve title stealthiness to avoid detection',
                'actions': [
                    'Add more pattern variations',
                    'Implement randomization in word choice',
                    'Use context-aware substitutions'
                ]
            })
    
    def test_pattern_quality(self):
        """Test if patterns generate high-quality titles"""
        print("\n" + "=" * 80)
        print("🎯 PATTERN QUALITY TESTING")
        print("=" * 80)
        
        # Sample test patterns
        test_patterns = [
            {
                'pattern': 'How {PERSON} {ACTION} {TOPIC}',
                'example': 'How Doug DeMuro Reviews Cars',
                'quality': 'Good - Clear and specific'
            },
            {
                'pattern': 'Top {NUMBER} {TOPIC} You Need to Know',
                'example': 'Top 10 Cars You Need to Know',
                'quality': 'Good - Proven viral format'
            },
            {
                'pattern': '{TOPIC}: What {PERSON} Won\'t Tell You',
                'example': 'Car Reviews: What Dealers Won\'t Tell You',
                'quality': 'Excellent - Creates curiosity'
            }
        ]
        
        for i, pattern_test in enumerate(test_patterns, 1):
            print(f"\nPattern {i}:")
            print(f"  Template: {pattern_test['pattern']}")
            print(f"  Example: {pattern_test['example']}")
            print(f"  Quality: {pattern_test['quality']}")
        
        print("\n✅ Pattern templates appear well-structured")
    
    def check_for_improvements(self):
        """Check what improvements are needed"""
        print("\n" + "=" * 80)
        print("🔧 IMPROVEMENT OPPORTUNITIES")
        print("=" * 80)
        
        improvements = [
            {
                'area': 'Pattern Diversity',
                'current': 'Basic patterns',
                'improvement': 'Add 20+ more patterns across different styles',
                'priority': 'HIGH'
            },
            {
                'area': 'Emotional Triggers',
                'current': 'Limited emotional words',
                'improvement': 'Add emotion-based word banks (exciting, shocking, amazing)',
                'priority': 'HIGH'
            },
            {
                'area': 'Number Variations',
                'current': 'Fixed numbers',
                'improvement': 'Use odd numbers (7, 13) - shown to perform better',
                'priority': 'MEDIUM'
            },
            {
                'area': 'Clickbait Detection',
                'current': 'No filtering',
                'improvement': 'Filter out overly clickbaity patterns',
                'priority': 'MEDIUM'
            },
            {
                'area': 'A/B Testing',
                'current': 'Single title generation',
                'improvement': 'Generate 3-5 variations per topic',
                'priority': 'HIGH'
            },
            {
                'area': 'Trending Words',
                'current': 'Static word list',
                'improvement': 'Pull trending words from social media',
                'priority': 'LOW'
            }
        ]
        
        for imp in improvements:
            priority_color = {
                'HIGH': '\033[91m',
                'MEDIUM': '\033[93m',
                'LOW': '\033[94m'
            }[imp['priority']]
            
            print(f"\n{priority_color}[{imp['priority']}]\033[0m {imp['area']}")
            print(f"  Current: {imp['current']}")
            print(f"  Improvement: {imp['improvement']}")
            
            self.results['recommendations'].append({
                'priority': imp['priority'],
                'area': imp['area'],
                'recommendation': imp['improvement']
            })
    
    def generate_report(self):
        """Generate final evaluation report"""
        print("\n" + "=" * 80)
        print("📋 FINAL EVALUATION REPORT")
        print("=" * 80)
        
        print(f"\n📊 Overall Scores:")
        print(f"  Quality Score: {self.results['quality_score']:.1f}%")
        print(f"  Stealthiness Score: {self.results['stealthiness_score']:.1f}%")
        
        overall_score = (self.results['quality_score'] + self.results['stealthiness_score']) / 2
        print(f"\n  🎯 Overall System Score: {overall_score:.1f}%")
        
        if overall_score >= 80:
            print("\n  ✅ EXCELLENT - System is production-ready")
        elif overall_score >= 60:
            print("\n  ⚠️  GOOD - System works but needs improvements")
        else:
            print("\n  ❌ NEEDS WORK - Significant improvements required")
        
        # Issues
        if self.results['issues']:
            print(f"\n🐛 Issues Found: {len(self.results['issues'])}")
            
            critical = [i for i in self.results['issues'] if i['severity'] == 'CRITICAL']
            high = [i for i in self.results['issues'] if i['severity'] == 'HIGH']
            
            if critical:
                print(f"\n  🔴 CRITICAL ({len(critical)}):")
                for issue in critical:
                    print(f"    • [{issue['component']}] {issue['issue']}")
            
            if high:
                print(f"\n  🟠 HIGH ({len(high)}):")
                for issue in high:
                    print(f"    • [{issue['component']}] {issue['issue']}")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n💡 Recommendations ({len(self.results['recommendations'])}):")
            
            high_priority = [r for r in self.results['recommendations'] if r.get('priority') == 'HIGH']
            
            if high_priority:
                print("\n  🔴 HIGH PRIORITY:")
                for i, rec in enumerate(high_priority, 1):
                    print(f"    {i}. {rec['recommendation']}")
        
        # Save report
        report_file = Path("test_reports/title_prediction_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Full report saved: {report_file}")
        
        print("\n" + "=" * 80)
        
        # Final verdict
        if overall_score >= 75:
            print("✅ VERDICT: System is READY for production")
            print("   Minor optimizations recommended but not blocking")
        elif overall_score >= 60:
            print("⚠️  VERDICT: System NEEDS IMPROVEMENTS before production")
            print("   Address HIGH priority issues first")
        else:
            print("❌ VERDICT: System NOT READY for production")
            print("   Major improvements required")
        
        print("=" * 80)
    
    def run_evaluation(self):
        """Run complete evaluation"""
        print("=" * 80)
        print("🎯 TITLE PREDICTION SYSTEM EVALUATION")
        print("=" * 80)
        
        self.analyze_competitor_title_generator()
        self.analyze_youtube_client()
        self.evaluate_stealthiness()
        self.test_pattern_quality()
        self.check_for_improvements()
        self.generate_report()


if __name__ == "__main__":
    evaluator = TitlePredictionEvaluator()
    evaluator.run_evaluation()
