import requests
from app import app, db, login_manager
from models import User, Keyword, Competitor
from flask_login import login_user

def verify_settings_api():
    print("🧪 Verifying Settings API interactions...")
    
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing

    with app.app_context():
        # Setup test user
        u = User.query.filter_by(username='settings_tester').first()
        if u: db.session.delete(u)
        db.session.commit()
        
        u = User(username='settings_tester', email='settings@test.com')
        u.set_password('password')
        db.session.add(u)
        db.session.commit()
        user_id = u.id
        print(f"✅ Created settings_tester (ID: {user_id})")

    # Use test client
    with app.test_client() as client:
        # Simulate login by logging in via a helper endpoint or bypassing
        # Since we disabled CSRF, normal login should work if endpoint is simple.
        # But even better, we can assume authentication if we can mock it, but test_client handles cookies.
        
        resp = client.post('/login', data={'username': 'settings_tester', 'password': 'password'}, follow_redirects=True)
        # Check if we are logged in. The response should contain dashboard content or "Dashboard"
        if resp.status_code == 200:
             print("✅ Login request successful (200 OK w/ redirect follow)")
        else:
             print(f"❌ Login failed: {resp.status_code}")
             return

        # 1. Add Keyword
        resp = client.post('/api/keywords', json={'keyword': 'test_kw', 'category': 'primary'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] == True
        assert data['data']['keyword'] == 'test_kw'
        assert data['data']['category'] == 'primary'
        kw_id = data['data']['id']
        print(f"✅ Added Keyword (ID: {kw_id})")
        
        # 2. Get Keywords
        resp = client.get('/api/keywords')
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]['keyword'] == 'test_kw'
        print("✅ Get Keywords verified")
        
        # 3. Toggle Keyword
        resp = client.post(f'/api/keywords/{kw_id}/toggle')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] == True
        assert data['enabled'] == False # Toggled from True
        print("✅ Toggle Keyword verified")
        
        # 4. Add Competitor
        resp = client.post('/api/competitors', json={'name': 'Test Comp', 'url': 'https://youtube.com/test'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] == True
        comp_id = data['data']['id']
        print(f"✅ Added Competitor (ID: {comp_id})")
        
        # 5. Toggle Competitor
        resp = client.post(f'/api/competitors/{comp_id}/toggle')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] == True
        assert data['enabled'] == False
        print("✅ Toggle Competitor verified")
    
    # Cleanup
    with app.app_context():
        u = User.query.get(user_id)
        if u:
            db.session.delete(u)
            db.session.commit()
        print("✅ Cleanup complete")
    
    print("\n🎉 SUCCESS: Settings API Verified!")

if __name__ == "__main__":
    verify_settings_api()
