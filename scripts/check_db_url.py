import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db

def check_db_url():
    with app.app_context():
        print(f"Flask Instance Path: {app.instance_path}")
        print(f"DB Engine URL: {db.engine.url}")
        
if __name__ == "__main__":
    check_db_url()
