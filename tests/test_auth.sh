#!/bin/bash

# ViralLens Authentication Testing Script
# Run this to test the authentication system

echo "🧪 ViralLens Authentication Testing"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run from project root."
    exit 1
fi

# Install dependencies
echo "📦 Step 1: Installing dependencies..."
pip3 install -q Flask Flask-Login Flask-SQLAlchemy Flask-Migrate email-validator python-dotenv Werkzeug gunicorn

# Initialize database
echo ""
echo "🗄️  Step 2: Initializing database..."
python3 << 'PYTHON'
from app import app, db
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")
PYTHON

# Create admin user
echo ""
echo "👤 Step 3: Creating admin user..."
python3 << 'PYTHON'
from app import app, db
from models import User
from datetime import datetime

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(email='admin@viralens.ai').first()
    
    if admin:
        print("ℹ️  Admin user already exists")
    else:
        # Adapted to match models.py (removed username, subscription_status, subscription_start)
        admin = User(
            email='admin@viralens.ai',
            full_name='Admin User',
            niche='general',
            subscription_tier='agency',
            runs_limit=-1,
            onboarding_completed=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")
        print("   Email: admin@viralens.ai")
        print("   Password: admin123")
PYTHON

echo ""
echo "🚀 Step 4: Starting Flask application..."
echo ""
echo "=================================================="
echo "🎯 ViralLens is now running!"
echo "=================================================="
echo ""
echo "📍 URLs to test:"
echo "   Landing page:  http://127.0.0.1:8000/"
echo "   Sign up:       http://127.0.0.1:8000/signup"
echo "   Login:         http://127.0.0.1:8000/login"
echo "   Dashboard:     http://127.0.0.1:8000/dashboard"
echo ""
echo "👤 Test credentials:"
echo "   Email: admin@viralens.ai"
echo "   Password: admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

# Start Flask app
python3 app.py
