
import sys
import os

print("Testing app startup...")
try:
    from app import app
    from models import db, User, ResearchRun
    
    print("Imports successful.")
    
    with app.app_context():
        print("Database URI:", app.config.get('SQLALCHEMY_DATABASE_URI'))
        print("User count:", User.query.count())
        # Test the daily usage method that was modified
        u = User.query.first()
        if u:
            print(f"Daily usage for {u.username}: {u.get_daily_usage()}")
        
    print("App startup verification PASSED.")
except Exception as e:
    print(f"App startup FAILED: {e}")
    import traceback
    traceback.print_exc()
