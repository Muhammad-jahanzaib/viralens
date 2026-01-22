#!/usr/bin/env python3
"""
ViralLens - Bulk User Deletion Script
Permanently deletes users whose username contains the word "user".
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

def delete_user_pattern(dry_run=True):
    with app.app_context():
        print(f"🔍 Searching for users with 'user' in username (Dry Run: {dry_run})...")
        
        # Find users with 'user' in username (case-insensitive)
        pattern = '%user%'
        target_users = User.query.filter(User.username.ilike(pattern)).all()
        
        if not target_users:
            print("✅ No matching users found.")
            return
            
        print(f"📊 Found {len(target_users)} users matching the pattern.")
        
        deleted_count = 0
        for user in target_users:
            try:
                # Security check: Ensure we don't delete an admin unless specificed
                if user.is_admin and user.username == 'admin':
                    print(f"⚠️  Skipping protected admin user: {user.username}")
                    continue
                
                if dry_run:
                    print(f"Draft Deletion: {user.username} ({user.email})")
                    deleted_count += 1
                else:
                    print(f"🗑️ Deleting user: {user.username}")
                    db.session.delete(user)
                    deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {user.username}: {e}")
        
        if not dry_run and deleted_count > 0:
            db.session.commit()
            print(f"✅ Successfully deleted {deleted_count} users.")
        elif dry_run:
            print(f"💡 Found {deleted_count} users to delete. Run with '--real' to perform deletion.")

if __name__ == "__main__":
    dry_run = "--real" not in sys.argv
    delete_user_pattern(dry_run=dry_run)
