from app import app, db, mail
from models import User, EmailLog
from utils.admin_utils import send_system_email

def test_email_system():
    with app.test_request_context():
        # Allow real email sending for testing
        app.config['MAIL_SUPPRESS_SEND'] = False
        app.config['SERVER_NAME'] = 'localhost'
        app.config['PREFERRED_URL_SCHEME'] = 'http'
        
        # 1. Find or create a test user
        recipient_email = 'peachprismllc50@gmail.com'
        test_user = User.query.filter((User.email == recipient_email) | (User.username == 'sendgrid_tester')).first()
        if not test_user:
            from werkzeug.security import generate_password_hash
            test_user = User(
                email=recipient_email,
                username='sendgrid_tester',
                password_hash=generate_password_hash('Password123!'),
                full_name='Test SendGrid System'
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"Created test user: {test_user.email}")
        else:
            # Ensure it has the right email for testing
            test_user.email = recipient_email
            db.session.commit()
        
        # 2. Test Welcome Email
        print("Testing Welcome Email...")
        success = send_system_email(
            test_user.email,
            "Welcome to ViralLens!",
            "welcome",
            user_id=test_user.id,
            name=test_user.full_name,
            status='pending'
        )
        print(f"Welcome email result: {'✅ Success' if success else '❌ Failed'}")
        
        # 3. Test Approval Email
        print("Testing Approval Email...")
        success = send_system_email(
            test_user.email,
            "Your account is approved!",
            "approval",
            user_id=test_user.id,
            name=test_user.full_name,
            tier='Pro'
        )
        print(f"Approval email result: {'✅ Success' if success else '❌ Failed'}")
        
        # 4. Verify Logs
        logs = EmailLog.query.filter_by(user_id=test_user.id).all()
        print(f"\nTotal logs for test user: {len(logs)}")
        for log in logs:
            print(f" - [{log.status.upper()}] {log.subject} (Template: {log.template})")
            
        if len(logs) >= 2:
            print("\n✅ Email notification system verified and logged successfully!")
        else:
            print("\n❌ Failed to verify email logs.")

if __name__ == "__main__":
    test_email_system()
