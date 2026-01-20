from app import app, db
from models import User

def test_admin_access():
    print("🛡️ Testing Admin Access...\n")
    
    with app.app_context():
        # 1. Check Admin User
        print("1. Verifying Admin User:")
        admin = User.query.filter_by(email='admin@viralens.ai').first()
        
        if admin:
            print(f"   ✅ Found Admin User: {admin.email}")
            print(f"   - Is Admin: {admin.is_admin}")
            print(f"   - Is Active: {admin.is_active}")
            print(f"   - Username: {admin.username}")
            print(f"   - Login: admin@viralens.ai")
            print(f"   - Password: Admin123!@# (Typical default)")
        else:
            print("   ❌ Admin user NOT FOUND!")
            return

        # 2. Check Admin Blueprint
        print("\n2. Verifying Admin Blueprint:")
        if 'admin' in app.blueprints:
            print(f"   ✅ 'admin' Blueprint is registered!")
            print(f"   - URL Prefix: {app.blueprints['admin'].url_prefix}")
        else:
            print("   ❌ 'admin' Blueprint NOT registered!")
            return

        # 3. List Admin Routes
        print("\n3. Registered Admin Routes:")
        admin_routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('admin.'):
                admin_routes.append(f"{rule.rule} -> {rule.endpoint}")
        
        if admin_routes:
            for route in sorted(admin_routes):
                print(f"   ✅ {route}")
            print(f"\n   Total Admin Routes: {len(admin_routes)}")
        else:
            print("   ❌ No admin routes found!")

if __name__ == "__main__":
    test_admin_access()
