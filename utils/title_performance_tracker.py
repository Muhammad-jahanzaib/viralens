"""
Track which titles users chose and their performance
Learn from user feedback to improve recommendations
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from utils.logger import logger
from models import db, TitlePerformance

class TitlePerformanceTracker:
    """
    Tracks performance of generated titles to improve future recommendations.
    Uses SQLite database via SQLAlchemy.
    """

    def __init__(self):
        """Initialize tracker"""
        # No local storage initialization needed for DB
        pass

    def record_title_usage(self, topic_id: str, chosen_title: str, pattern_type: str = "unknown", competitor_source: str = None) -> Dict:
        """
        Record that a user chose to use a specific title.
        
        Args:
            topic_id: ID of the generated topic
            chosen_title: The specific title text used
            pattern_type: The pattern type (e.g. "Question", "Number")
            competitor_source: Name of competitor if modeled after one
            
        Returns:
            Dict with record ID and success status
        """
        try:
            record = TitlePerformance(
                topic_id=topic_id,
                title=chosen_title,
                pattern_type=pattern_type,
                competitor_source=competitor_source,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"Recorded title usage: '{chosen_title}' (Pattern: {pattern_type}) - ID: {record.id}")
            
            return {
                "success": True,
                "id": record.id
            }
            
        except Exception as e:
            logger.error(f"Error recording title usage: {e}")
            db.session.rollback()
            return {"success": False, "error": str(e)}

    def report_performance(self, record_id: int, views: int, ctr: float, avd: float) -> bool:
        """
        Update performance metrics for a recorded title.
        
        Args:
            record_id: Database ID of the title record
            views: Number of views
            ctr: Click-Through Rate (percentage)
            avd: Average View Duration (percentage)
            
        Returns:
            True if successful
        """
        try:
            record = TitlePerformance.query.get(int(record_id))
            if not record:
                logger.warning(f"Title record {record_id} not found")
                return False
                
            record.views = views
            record.ctr = ctr
            record.avd = avd
            
            # Simple confidence score calculation
            # Weights: CTR (40%), AVD (40%), Views (20%) - Normalized roughly to 0-100
            # Heuristic: 10% CTR is great (100 pts), 50% AVD is great (100 pts)
            score = min(100, (ctr * 10 * 0.4) + (avd * 2 * 0.4) + (min(views, 10000) / 100 * 0.2))
            record.confidence_score = int(score)
            
            record.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Updated performance for title {record_id}: CTR={ctr}%, Score={int(score)}")
            return True
            
        except Exception as e:
            logger.error(f"Error reporting performance: {e}")
            db.session.rollback()
            return False

    def get_best_performing_patterns(self, top_n: int = 5) -> List[Dict]:
        """
        Get the most successful title patterns based on historical performance.
        
        Returns:
            List of dicts with pattern stats
        """
        try:
            # Group by pattern_type and calculate averages using SQL
            from sqlalchemy import func
            
            stats = db.session.query(
                TitlePerformance.pattern_type,
                func.count(TitlePerformance.id).label('count'),
                func.avg(TitlePerformance.confidence_score).label('avg_score'),
                func.avg(TitlePerformance.ctr).label('avg_ctr')
            ).group_by(TitlePerformance.pattern_type).having(func.count(TitlePerformance.id) > 0).all()
            
            # Format results
            results = []
            for pattern, count, avg_score, avg_ctr in stats:
                if not pattern or pattern == "unknown":
                    continue
                    
                results.append({
                    "pattern": pattern,
                    "usage_count": count,
                    "avg_score": round(avg_score or 0, 1),
                    "avg_ctr": round(avg_ctr or 0, 1),
                    "recommendation": "High performing" if (avg_score or 0) > 70 else "Average"
                })
            
            # Sort by score descending
            results.sort(key=lambda x: x["avg_score"], reverse=True)
            return results[:top_n]
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return []
    
    def get_competitor_success_rate(self, competitor: str) -> Dict:
        """
        Get success rate for titles inspired by specific competitor
        
        Args:
            competitor: Competitor channel name
            
        Returns:
            Dict with success statistics
        """
        try:
            from sqlalchemy import func
            
            stats = db.session.query(
                func.count(TitlePerformance.id),
                func.avg(TitlePerformance.views),
                func.avg(TitlePerformance.ctr)
            ).filter(
                TitlePerformance.competitor_source == competitor,
                TitlePerformance.confidence_score != None
            ).first()
            
            count, avg_views, avg_ctr = stats
            
            if not count:
                return {
                    'competitor': competitor,
                    'titles_used': 0,
                    'avg_performance': 'NO_DATA'
                }
            
            return {
                'competitor': competitor,
                'titles_used': count,
                'avg_views': int(avg_views or 0),
                'avg_ctr': round(avg_ctr or 0, 2),
                'recommendation': self._get_recommendation(avg_views or 0, avg_ctr or 0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing competitor success: {e}")
            return {'competitor': competitor, 'error': str(e)}

    def _get_recommendation(self, avg_views: float, avg_ctr: float) -> str:
        """Generate recommendation based on performance"""
        
        if avg_views > 50000 and avg_ctr > 10:
            return "🔥 EXCELLENT - Keep using this competitor's patterns"
        elif avg_views > 20000 and avg_ctr > 8:
            return "✅ GOOD - Solid performer"
        elif avg_views > 10000:
            return "📈 DECENT - Room for improvement"
        else:
            return "⚠️ UNDERPERFORMING - Consider other competitors"
