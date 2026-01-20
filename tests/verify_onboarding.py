import requests
from app import app, db
from models import User, Keyword, Competitor, UserConfig

def verify_onboarding_logic():
    print("🧪 Verifying Onboarding Logic...")
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False 

    with app.app_context():
        # Setup test user
        u = User.query.filter_by(username='onboarding_tester').first()
        if u: db.session.delete(u)
        db.session.commit()
        
        u = User(username='onboarding_tester', email='onboard@test.com')
        u.set_password('password')
        u.onboarding_completed = False # Explicitly False
        db.session.add(u)
        db.session.commit()
        user_id = u.id
        print(f"✅ Created onboarding_tester (ID: {user_id}), onboarding_completed=False")

    # Add a route to force login for testing
    @app.route('/test-login/<int:user_id>')
    def test_login(user_id):
        from flask_login import login_user
        user = User.query.get(user_id)
        login_user(user)
        return "Logged in"

    with app.test_client() as client:
        # Force login via our backdoor
        client.get(f'/test-login/{user_id}')
        
        # Now check dashboard. 
        # Since we are "logged in", dashboard should see us.
        # If we are NOT onboarding_completed, it redirects to /onboarding
        resp = client.get('/dashboard', follow_redirects=False)
        print(f"DEBUG: Status={resp.status_code}, Location={resp.location}")
        
        # If it redirects to login, then login failed.
        if '/login' in resp.location:
             print("❌ Login failed in test script")
             return

        assert resp.status_code == 302
        assert '/onboarding' in resp.location
        print("✅ Dashboard redirect to /onboarding verified")
        
        # 2. Call Smart Setup (Mocked AI response mainly, but since we rely on external API, we might hit it or fail if no key.
        # Actually, if we don't have ANTHROPIC_API_KEY set in env, it differs.
        # Let's verify the 'Skip' flow first as it is deterministic.
        
        resp = client.post('/api/complete-onboarding')
        assert resp.status_code == 200
        assert resp.get_json()['success'] == True
        print("✅ /api/complete-onboarding success")
        
        # 3. Verify User State
        with app.app_context():
            u = User.query.get(user_id)
            assert u.onboarding_completed == True
            print("✅ User onboarding_completed is True in DB")
            
        # 4. Access Dashboard - Should 200 OK now
        resp = client.get('/dashboard')
        assert resp.status_code == 200
        print("✅ Dashboard access verified (No redirect)")
        
    # Cleanup
    with app.app_context():
        u = User.query.get(user_id)
        if u:
            db.session.delete(u)
            db.session.commit()
        print("✅ Cleanup complete")
        
    print("\n🎉 SUCCESS: Onboarding Flow Verified!")

if __name__ == "__main__":
    verify_onboarding_logic()
