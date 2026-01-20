import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User
from datetime import datetime

with app.app_context():
    # Check if test user already exists
    existing = User.query.filter_by(username='testpending').first()
    if existing:
        print(f"Test user already exists: {existing.username} (ID: {existing.id})")
        print(f"Approval status: {existing.approval_status}")
        
        # Update to pending if needed
        if existing.approval_status != 'pending':
            existing.approval_status = 'pending'
            db.session.commit()
            print("Updated existing user to pending status")
    else:
        # Create new pending user
        test_user = User(
            username='testpending',
            email='testpending@viralens.test',
            full_name='Test Pending User',
            niche='Testing Approval Workflow',
            subscription_tier='free',
            approval_status='pending',  # Set to pending
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_user.set_password('TestPass123!')
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✅ Test pending user created successfully!")
        print(f"   Username: testpending")
        print(f"   Email: testpending@viralens.test")
        print(f"   Password: TestPass123!")
        print(f"   Approval Status: {test_user.approval_status}")
        print(f"   User ID: {test_user.id}")
    
    # Show all pending users
    print("\n--- All Pending Users ---")
    pending_users = User.query.filter_by(approval_status='pending').all()
    for user in pending_users:
        days_waiting = (datetime.utcnow() - user.created_at).days if user.created_at else 0
        print(f"  - {user.username} ({user.email}) - Waiting: {days_waiting} days")
    print(f"\nTotal pending: {len(pending_users)}")
