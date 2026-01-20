import unittest
from datetime import datetime
from utils.research_processor import process_research_results

class MockResearchRun:
    def __init__(self, id, topics_data, sources_successful=5, runtime_seconds=30.0):
        self.id = id
        self.topics_data = topics_data
        self.sources_successful = sources_successful
        self.runtime_seconds = runtime_seconds
        self.created_at = datetime.now()

class TestResearchProcessor(unittest.TestCase):
    def test_dynamic_mapping(self):
        # Mock Claude output structure
        ai_data = {
            "topic_recommendations": [
                {
                    "rank": 1,
                    "title": "Quantum Computing is Closer Than You Think",
                    "video_type": "Evergreen/Deep Dive",
                    "hook": "Imagine a computer a billion times faster...",
                    "key_points": ["Qubits vs Bits", "Error correction", "Future impact"],
                    "evidence_sources": [
                        {"name": "Nature Journal", "platform": "News", "hours_ago": 2},
                        {"name": "ScienceDaily", "platform": "News", "hours_ago": 5}
                    ],
                    "viral_potential": "HIGH - immense interest in breakthroughs",
                    "publishing_priority": 9
                }
            ],
            "trending_themes": ["Quantum Supremacy", "AI integration"],
            "competitor_insights": "Competitors are missing technical depth."
        }
        
        run = MockResearchRun(id=123, topics_data=ai_data)
        display_data = process_research_results(run)
        
        # Verify basic metadata
        self.assertEqual(display_data['metadata']['run_id'], 123)
        self.assertEqual(len(display_data['topics']), 1)
        
        # Verify topic mapping
        topic = display_data['topics'][0]
        self.assertEqual(topic['title'], "Quantum Computing is Closer Than You Think")
        self.assertEqual(topic['overall_score'], 90) # priority 9 * 10
        self.assertEqual(topic['competition_level'], 'low') # HIGH potential -> low competition gap
        
        # Verify signals
        self.assertEqual(len(topic['confidence_signals']), 2)
        self.assertIn("Nature Journal", topic['confidence_signals'][0]['source'])
        
        # Verify metrics (synthsized)
        self.assertEqual(len(topic['metrics']), 4)
        self.assertTrue(len(topic['metrics'][0]['trend_data']) == 8)
        
        # Verify methodology
        self.assertEqual(len(display_data['methodology']), 5)
        
        # Verify enhanced fields
        self.assertEqual(display_data['enhanced']['trending_themes'], ["Quantum Supremacy", "AI integration"])

    def test_legacy_support(self):
        # Mock legacy list structure
        legacy_data = [
            {"title": "Old Topic", "publishing_priority": 7}
        ]
        run = MockResearchRun(id=456, topics_data=legacy_data)
        display_data = process_research_results(run)
        
        self.assertEqual(len(display_data['topics']), 1)
        self.assertEqual(display_data['topics'][0]['title'], "Old Topic")
        self.assertEqual(display_data['topics'][0]['overall_score'], 70)

if __name__ == '__main__':
    unittest.main()
