import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User
from datetime import datetime

with app.app_context():
    # Check if test user already exists and remove if so to start fresh
    existing = User.query.filter_by(username='testpending2').first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    # Create new pending user
    test_user = User(
        username='testpending2',
        email='testpending2@viralens.test',
        full_name='Test Pending User 2',
        niche='Testing Rejection',
        subscription_tier='free',
        approval_status='pending',
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_user.set_password('TestPass123!')
    
    db.session.add(test_user)
    db.session.commit()
    
    print(f"✅ Test pending user 2 created successfully!")
    print(f"   Username: testpending2")
    print(f"   Status: pending")
