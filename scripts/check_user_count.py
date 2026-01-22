import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

def check_count():
    with app.app_context():
        count = User.query.count()
        print(f"User Count: {count}")
        if count > 0:
            users = User.query.limit(5).all()
            for u in users:
                print(f"ID: {u.id}, Username: {u.username}")

if __name__ == "__main__":
    check_count()
