import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, User

# Disable CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

def test_approval_flow():
    # 0. SETUP: Ensure user is pending
    with app.app_context():
        u = User.query.filter_by(username='testpending').first()
        if u:
            u.approval_status = 'pending'
            db.session.commit()
            print("0. SETUP: Reset 'testpending' to pending status.")

    with app.test_client() as client:
        # 1. Try to login as pending user
        print("1. Attempting login as 'testpending' (Expected: Blocked)")
        response = client.post('/login', data={'email': 'testpending', 'password': 'Password123!'}, follow_redirects=True)
        html = response.data.decode('utf-8')
        
        if "Your account is awaiting admin approval" in html:
            print("   SUCCESS: Login blocked with correct message.")
        else:
            print("   FAILURE: Login not blocked or wrong message.")
            if "Invalid email or password" in html:
                 print("   NOTE: Credentials might be wrong. Resetting password to Password123!")
                 with app.app_context():
                     u = User.query.filter_by(username='testpending').first()
                     u.set_password('Password123!')
                     db.session.commit()
                 # Retry
                 response = client.post('/login', data={'email': 'testpending', 'password': 'Password123!'}, follow_redirects=True)
                 html = response.data.decode('utf-8')
                 if "Your account is awaiting admin approval" in html:
                     print("   SUCCESS: Login blocked with correct message (after pw reset).")
                 else:
                     print("   FAILURE (Retry): Still failing.")

            
        # 2. Approve user
        print("\n2. Approving user 'testpending' via Admin Action...")
        with app.app_context():
            user = User.query.filter_by(username='testpending').first()
            if user:
                user.approval_status = 'approved'
                db.session.commit()
                print("   User approved in DB.")
            else:
                print("   User 'testpending' not found!")
                return

        # 3. Try to login again
        print("\n3. Attempting login as 'testpending' (Expected: Success)")
        response = client.post('/login', data={'email': 'testpending', 'password': 'Password123!'}, follow_redirects=True)
        html = response.data.decode('utf-8')
        
        if "Welcome back, testpending!" in html or "Dashboard" in html or "onboarding" in html:
            print("   SUCCESS: Login successful.")
        else:
            print("   FAILURE: Login failed after approval.")
            print("   Page content excerpt: " + html[:500])

if __name__ == "__main__":
    test_approval_flow()
