import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash

def check_active_admin():
    db_path = 'instance/viralens.db'
    if not os.path.exists(db_path):
        print(f"❌ Active database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT id, username, email, is_admin, password_hash, approval_status, is_active FROM users WHERE is_admin = 1;")
        admins = cursor.fetchall()
        
        if not admins:
            print("⚠️ No admin users found in the active database.")
        else:
            print(f"✅ Found {len(admins)} admin(s) in active DB:")
            for admin in admins:
                print(f"ID: {admin[0]}")
                print(f"Username: {admin[1]}")
                print(f"Email: {admin[2]}")
                print(f"Status: {admin[5]}")
                print(f"Is Active: {admin[6]}")
                print(f"Password Hash: {admin[3][:20]}...")
                print("-" * 20)
                
        conn.close()
    except Exception as e:
        print(f"❌ Error checking active DB: {e}")

if __name__ == "__main__":
    check_active_admin()
