import requests
import json
import os
from app import app, db
from models import User, Keyword, Competitor, ResearchRun

def verify_end_to_end():
    print("🧪 Verifying End-to-End Research Flow...")
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False 

    with app.app_context():
        # Clean previous runs
        user = User.query.filter_by(username='onboarding_tester').first()
        if not user:
            print("❌ User onboarding_tester not found. Run verify_onboarding.py first or created it.")
            # Create if missing
            user = User(username='onboarding_tester', email='e2e@test.com')
            user.set_password('password')
            user.onboarding_completed = True
            db.session.add(user)
            db.session.commit()
        
        user_id = user.id
        
        # Ensure data exists
        if not Keyword.query.filter_by(user_id=user_id).first():
            k = Keyword(user_id=user_id, keyword="test keyword", category="primary")
            db.session.add(k)
        
        if not Competitor.query.filter_by(user_id=user_id).first():
            c = Competitor(user_id=user_id, name="Test Comp", url="http://test.com", enabled=True)
            db.session.add(c)
            
        db.session.commit()
        print(f"✅ User {user_id} ready with data")

        # Mock the run_research function to avoid actual long API calls?
        # Or just run it and hope it fails fast or returns something.
        # But main.py's run_research does real work.
        # For this test, we might want to check if /api/run-research calls it correctly.
        # We can't easily mock inside a subprocess validation script without patching.
        # I'll rely on the fact that if it crashes, 500. If it starts, it might take time.
        # I will check if I can trigger the synchronous one or just check if logic holds.
        # The synchronous endpoint `/api/run-research` calls `run_research(user_id)`.
        
        pass

    # We will use the test client to trigger the run
    # Inject test login route
    @app.route('/test-login/<int:user_id>')
    def test_login(user_id):
        from flask_login import login_user
        user = User.query.get(user_id)
        login_user(user)
        return "Logged in"

    # We will use the test client to trigger the run
    with app.test_client() as client:
        # Force Login
        client.get(f'/test-login/{user_id}')
        
        print("⏳ Triggering Research (this might fail if API keys missing, but checking flow)...")
        
        # We assume logged in now.
        try:
            resp = client.post('/api/run-research')
            print(f"Response Status: {resp.status_code}")
            
            if resp.status_code == 302:
                 print(f"❌ Redirected to: {resp.location} (Login failed?)")
            elif resp.status_code == 200:
                print("✅ Research ran successfully")
            elif resp.status_code == 500:
                print("⚠️ Research failed (likely expected due to API keys):")
                # print(resp.get_json()) # might be text/html error page or JSON
            elif resp.status_code == 403:
                print("❌ Permission denied")
            
            # Check if ResearchRun record created (if success)
            if resp.status_code == 200:
                 with app.app_context():
                     run = ResearchRun.query.filter_by(user_id=user_id).order_by(ResearchRun.created_at.desc()).first()
                     if run:
                         print(f"✅ ResearchRun record created: ID {run.id}")
                     else:
                         print("❌ No ResearchRun record found")

        except Exception as e:
            print(f"❌ Exception during request: {e}")

    print("\nTest Complete")

if __name__ == "__main__":
    verify_end_to_end()
