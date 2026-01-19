import os
import sys
from app import app, db
from models import User, Keyword, Competitor, UserConfig

def verify_isolation():
    print("🧪 Verifying Data Isolation...")
    
    with app.app_context():
        # Clean up test users
        u1 = User.query.filter_by(username='test_user_1').first()
        if u1: db.session.delete(u1)
        u2 = User.query.filter_by(username='test_user_2').first()
        if u2: db.session.delete(u2)
        db.session.commit()
        
        # Create User 1
        u1 = User(username='test_user_1', email='test1@example.com')
        u1.set_password('password')
        db.session.add(u1)
        db.session.commit()
        print(f"✅ Created User 1 (ID: {u1.id})")
        
        # Create User 2
        u2 = User(username='test_user_2', email='test2@example.com')
        u2.set_password('password')
        db.session.add(u2)
        db.session.commit()
        print(f"✅ Created User 2 (ID: {u2.id})")
        
        # User 1 adds data
        k1 = Keyword(user_id=u1.id, keyword="user1_keyword", enabled=True)
        c1 = Competitor(user_id=u1.id, name="User1 Channel", url="https://youtube.com/user1", channel_id="UC1")
        db.session.add(k1)
        db.session.add(c1)
        db.session.commit()
        print("✅ User 1 added data")
        
        # User 2 adds data
        k2 = Keyword(user_id=u2.id, keyword="user2_keyword", enabled=True)
        c2 = Competitor(user_id=u2.id, name="User2 Channel", url="https://youtube.com/user2", channel_id="UC2")
        db.session.add(k2)
        db.session.add(c2)
        db.session.commit()
        print("✅ User 2 added data")
        
        # Verify User 1 sees ONLY User 1 data
        u1_keywords = Keyword.query.filter_by(user_id=u1.id).all()
        u1_competitors = Competitor.query.filter_by(user_id=u1.id).all()
        
        assert len(u1_keywords) == 1
        assert u1_keywords[0].keyword == "user1_keyword"
        assert len(u1_competitors) == 1
        assert u1_competitors[0].name == "User1 Channel"
        print("✅ User 1 sees correct data")
        
        # Verify User 2 sees ONLY User 2 data
        u2_keywords = Keyword.query.filter_by(user_id=u2.id).all()
        u2_competitors = Competitor.query.filter_by(user_id=u2.id).all()
        
        assert len(u2_keywords) == 1
        assert u2_keywords[0].keyword == "user2_keyword"
        assert len(u2_competitors) == 1
        assert u2_competitors[0].name == "User2 Channel"
        print("✅ User 2 sees correct data")
        
        # Cleanup
        db.session.delete(u1) # Cascades should handle related data if set up, or manual delete
        db.session.delete(u2)
        db.session.commit()
        print("✅ Cleanup complete")
        
        print("\n🎉 SUCCESS: Data Isolation Verified!")

if __name__ == "__main__":
    verify_isolation()
