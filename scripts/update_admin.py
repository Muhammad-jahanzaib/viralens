import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app import app, db
from models import User

def update_admin_password(password):
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("⚠️ Admin user 'admin' not found. Creating one...")
            admin = User(
                username='admin',
                email='admin@viralens.ai',
                is_admin=True,
                is_active=True,
                approval_status='approved'
            )
            db.session.add(admin)
        
        print(f"Updating admin: {admin.username} ({admin.email})")
        admin.set_password(password)
        admin.is_active = True
        admin.approval_status = 'approved'
        admin.is_admin = True
        
        db.session.commit()
        print("✅ Admin password and status updated successfully!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/update_admin.py <new_password>")
        sys.exit(1)
    
    new_pwd = sys.argv[1]
    update_admin_password(new_pwd)
