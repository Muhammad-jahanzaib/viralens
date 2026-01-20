import os
import sys
from app import app, db
from models import User, AdminLog, SystemSettings, UserActivity
import inspect
import utils.admin_utils as admin_utils
import admin_routes

def check_file(path):
    exists = os.path.exists(path)
    print(f"[{'✅' if exists else '❌'}] File exists: {path}")
    return exists

def verify_all():
    print("🔍 Starting Final Verification Check...\n")
    
    with app.app_context():
        # 1. Database Columns
        print("1. Checking Database Schema...")
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('users')]
        has_admin = 'is_admin' in columns
        has_active = 'is_active' in columns
        print(f"[{'✅' if has_admin else '❌'}] Column 'is_admin' exists")
        print(f"[{'✅' if has_active else '❌'}] Column 'is_active' exists")
        
        # 2. Admin User
        print("\n2. Checking Admin User...")
        admin = User.query.filter_by(email='admin@viralens.ai').first()
        if admin:
            print(f"[{'✅' if admin else '❌'}] Admin user found: {admin.email}")
        else:
            print("[❌] Admin user NOT found")

        # 3. Models
        print("\n3. Checking Models...")
        print(f"[{'✅' if inspect.isclass(AdminLog) else '❌'}] Model AdminLog exists")
        print(f"[{'✅' if inspect.isclass(SystemSettings) else '❌'}] Model SystemSettings exists")
        print(f"[{'✅' if inspect.isclass(UserActivity) else '❌'}] Model UserActivity exists")

        # 4. Utils
        print("\n4. Checking Utils...")
        check_file('utils/admin_utils.py')
        required_funcs = ['admin_required', 'log_admin_action', 'get_system_stats']
        for func in required_funcs:
            has_func = hasattr(admin_utils, func)
            print(f"[{'✅' if has_func else '❌'}] Function '{func}' exists in utils")

        # 5. Routes
        print("\n5. Checking Routes...")
        check_file('admin_routes.py')
        route_count = len([r for r in app.url_map.iter_rules() if r.endpoint.startswith('admin.')])
        print(f"[{'✅' if route_count >= 14 else '❌'}] Admin routes registered: {route_count} (Expected 14+)")

        # 6. Templates
        print("\n6. Checking Templates...")
        templates = [
            'templates/base.html',
            'templates/admin/dashboard.html',
            'templates/admin/users.html',
            'templates/admin/user_detail.html',
            'templates/admin/research_runs.html',
            'templates/admin/logs.html',
            'templates/admin/settings.html',
            'templates/admin/analytics.html'
        ]
        for t in templates:
            check_file(t)

        # 7. App Registration
        print("\n7. Checking App Registration...")
        is_registered = 'admin' in app.blueprints
        print(f"[{'✅' if is_registered else '❌'}] Admin blueprint registered in app")

        # 8. URL Access
        print("\n8. Checking URL Access...")
        with app.test_client() as client:
            # Check login redirect (since we are not logged in)
            resp = client.get('/admin/dashboard')
            # 302 Found (Redirect) means route exists and auth is working
            print(f"[{'✅' if resp.status_code == 302 else '❌'}] /admin/dashboard exists and protects access (Status: {resp.status_code})")

if __name__ == "__main__":
    verify_all()
