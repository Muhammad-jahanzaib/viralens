import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from utils.admin_utils import send_system_email

def test_email():
    with app.app_context():
        print("🔍 Checking Email Configuration...")
        print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"MAIL_USERNAME: {'SET' if app.config.get('MAIL_USERNAME') else 'NOT SET'}")
        print(f"MAIL_PASSWORD: {'SET' if app.config.get('MAIL_PASSWORD') else 'NOT SET'}")
        print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
        recipient = input("Enter a test recipient email address: ")
        print(f"📧 Sending test email to {recipient}...")
        
        success = send_system_email(
            recipient,
            "ViralLens Email Test ✅",
            "welcome", # Reuse welcome template
            name="Tester",
            status="approved"
        )
        
        if success:
            print("🎉 Success! Email sent and logged.")
        else:
            print("❌ Failure: Email sending failed. Check terminal output for errors.")

if __name__ == "__main__":
    test_email()
