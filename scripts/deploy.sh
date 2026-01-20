#!/bin/bash

echo "=========================================="
echo "  VIRALENS - DEPLOY FIXED VERSION"
echo "=========================================="
echo ""

# Step 1: Backup current app.py
echo "Step 1/5: Backing up current app.py..."
if [ -f "app.py" ]; then
    cp app.py app_backup_$(date +%Y%m%d_%H%M%S).py
    echo "✅ Backup created: app_backup_$(date +%Y%m%d_%H%M%S).py"
else
    echo "⚠️  No existing app.py found (first deployment)"
fi

# Step 2: Deploy fixed version
echo ""
echo "Step 2/5: Verifying app.py..."
# Assumes app.py is ALREADY fixed by Agent
if grep -q "ResearchOrchestrator(user_id=current_user.id)" app.py; then
    echo "✅ app.py is already the fixed version"
else
    echo "⚠️  app.py might be old version. Please check."
fi

# Step 3: Verify models
echo ""
echo "Step 3/5: Checking database models..."
if grep -q "class Keyword" models.py; then
    echo "✅ models.py contains Keyword model"
else
    echo "⚠️  models.py missing Keyword model!"
fi

# Step 4: Optional database reset
echo ""
echo "Step 4/5: Database setup..."
read -p "Do you want to RESET the database? (deletes all data) [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f viralens.db
    echo "✅ Database reset"
    # Re-init DB
    python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
    echo "✅ Database re-initialized"
else
    echo "⏭️  Keeping existing database"
fi

# Step 5: Install dependencies
echo ""
echo "Step 5/5: Checking dependencies..."
if ! python3 -c "import flask_login" &> /dev/null; then
    echo "Installing missing dependencies..."
    pip3 install -q flask flask-login flask-sqlalchemy flask-migrate
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "=========================================="
echo "  ✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start server:  python3 app.py"
echo "2. Run tests:     python3 test_comprehensive.py"
echo "3. Open browser:  http://127.0.0.1:8000"
echo ""
echo "Expected: All tests should pass ✅"
echo ""
