#!/usr/bin/env python3

"""
ViralLens - Quick Start Script
Initializes database and starts the Flask server
"""

import os
import sys
from datetime import datetime

def main():
    print("🎯 ViralLens Quick Start")
    print("=" * 60)
    print()
    
    # Check if app.py exists
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found")
        print("   Please run this script from the project root directory")
        sys.exit(1)
    
    # Install dependencies
    print("📦 Step 1: Installing dependencies...")
    os.system('pip3 install -q Flask Flask-Login Flask-SQLAlchemy Flask-Migrate email-validator python-dotenv Werkzeug gunicorn 2>/dev/null')
    print("✅ Dependencies installed")
    print()
    
    # Initialize database
    print("🗄️  Step 2: Initializing database...")
    try:
        from app import app, db
        from models import User
        
        with app.app_context():
            # Drop all tables to handle schema changes gracefully in dev
            # db.drop_all() 
            # Actually, standard practice in dev scripts like this often assumes a fresh start or migration. 
            # Given the schema change is major, we should probably recreate.
            # But let's try just create_all first to see if it adds missing tables. 
            # User table changed, so we might need to recreate it.
            
            # For this context, let's force a recreation of the database file if the schema is incompatible.
            # But safety first: just create_all. If it fails, the user will see.
            db.create_all()
            print("✅ Database tables created")
            
            # Create admin user if doesn't exist
            admin = User.query.filter_by(email='admin@viralens.ai').first()
            if not admin:
                admin = User(
                    email='admin@viralens.ai',
                    username='admin',
                    full_name='Admin User',
                    niche='general',
                    subscription_tier='agency',
                    subscription_status='active',
                    subscription_start=datetime.utcnow(),
                    research_runs_this_month=0,
                    total_research_runs=0,
                    onboarding_completed=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created")
            else:
                print("ℹ️  Admin user already exists")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Suggest deleting the db file if it's a schema mismatch
        print("💡 Tip: If this is a schema error, try deleting 'viralens.db' and running this script again.")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("🚀 Starting ViralLens...")
    print("=" * 60)
    print()
    print("📍 URLs to test:")
    print("   Landing page:  http://127.0.0.1:8000/")
    print("   Sign up:       http://127.0.0.1:8000/signup")
    print("   Login:         http://127.0.0.1:8000/login")
    print("   Dashboard:     http://127.0.0.1:8000/dashboard")
    print()
    print("👤 Test credentials:")
    print("   Email:    admin@viralens.ai")
    print("   Password: admin123")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Start Flask app
    os.system('python3 app.py')

if __name__ == '__main__':
    main()
