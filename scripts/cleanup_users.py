#!/usr/bin/env python3
"""
ViralLens - Database Cleanup Script
Clears approved users except those approved today and specific exceptions.
"""

import sys
import os
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

def cleanup_users(dry_run=True):
    with app.app_context():
        print(f"🔍 Starting database cleanup (Dry Run: {dry_run})...")
        
        # Current date in UTC
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Exception emails
        exceptions = ['zaib.ch19@gmail.com']
        
        # Find approved users
        approved_users = User.query.filter_by(approval_status='approved').all()
        
        users_to_delete = []
        for user in approved_users:
            # Check if it's an exception
            if user.email in exceptions:
                print(f"Skipping exception: {user.email}")
                continue
            
            # Check if approved today
            if user.approved_at and user.approved_at >= today_start:
                print(f"Skipping recently approved: {user.email} (Approved at {user.approved_at})")
                continue
                
            # Check if user is admin (safety feature)
            if user.is_admin:
                print(f"Skipping admin: {user.email}")
                continue
                
            users_to_delete.append(user)
        
        print(f"📊 Found {len(users_to_delete)} users to delete.")
        
        if dry_run:
            for user in users_to_delete:
                print(f"Draft Deletion: {user.email} (ID: {user.id})")
        else:
            for user in users_to_delete:
                print(f"🗑️ Deleting user: {user.email}")
                db.session.delete(user)
            
            db.session.commit()
            print(f"✅ Successfully deleted {len(users_to_delete)} users.")

if __name__ == "__main__":
    dry_run = "--real" not in sys.argv
    cleanup_users(dry_run=dry_run)
    
    if dry_run:
        print("\n💡 Run with '--real' to actually perform deletions.")
