
import sys
import os

# Add parent directory to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Competitor
from config import YOUTUBE_API_KEY
from utils.youtube_validator import resolve_channel_id

def fix_missing_ids():
    """
    Find competitors with missing Channel IDs and attempt to resolve them
    using the improved validator logic.
    """
    print("="*60)
    print("YouTube Channel ID Fixer")
    print("="*60)
    
    with app.app_context():
        # Query for missing IDs (Null or Empty)
        competitors = Competitor.query.filter(
            (Competitor.channel_id == None) | 
            (Competitor.channel_id == '')
        ).all()
        
        if not competitors:
            print("✅ No competitors found with missing Channel IDs.")
            return

        print(f"Found {len(competitors)} competitors with missing IDs.")
        print("Attempting validation...")
        
        fixed_count = 0
        failed_count = 0
        
        for comp in competitors:
            print(f"\nProcessing: {comp.name}")
            print(f"  URL: {comp.url}")
            
            # Try to resolve
            new_id = resolve_channel_id(comp.url, YOUTUBE_API_KEY)
            
            if new_id:
                old_id = comp.channel_id
                comp.channel_id = new_id
                print(f"  ✅ RESOLVED: {new_id}")
                fixed_count += 1
            else:
                print(f"  ❌ FAILED: Could not resolve ID.")
                failed_count += 1
                
        if fixed_count > 0:
            print(f"\nCommitting {fixed_count} updates to database...")
            try:
                db.session.commit()
                print("✅ Database updated successfully.")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error saving to database: {e}")
        else:
            print("\nNo resolutions were successful.")
            
        print("\nSummary:")
        print(f"  Fixed: {fixed_count}")
        print(f"  Failed: {failed_count}")
        print("="*60)

if __name__ == "__main__":
    if not YOUTUBE_API_KEY:
        print("❌ Error: YOUTUBE_API_KEY not set in config/env.")
    else:
        fix_missing_ids()
