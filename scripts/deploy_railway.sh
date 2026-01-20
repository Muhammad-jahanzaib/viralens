#!/bin/bash

echo "🚀 VIRALENS - Railway Deployment Script"
echo "========================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - VIRALENS MVP"
fi

# Create Procfile for Railway
echo "📝 Creating Procfile..."
cat > Procfile << 'PROC'
web: gunicorn app:app --timeout 120 --workers 2 --bind 0.0.0.0:$PORT
PROC

# Create requirements.txt with production dependencies
echo "📝 Creating/updating requirements.txt..."
cat > requirements.txt << 'REQ'
Flask==3.0.0
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
requests==2.31.0
google-api-python-client==2.108.0
beautifulsoup4==4.12.2
gunicorn==21.2.0
python-dotenv==1.0.0
lxml==4.9.3
anthropic==0.45.0
tenacity==8.5.0
feedparser==6.0.11
newsapi-python==0.2.7
pytrends==4.9.2
tweepy==4.14.0
pandas==2.2.0
isodate==0.6.1
REQ

# Create runtime.txt
echo "📝 Creating runtime.txt..."
echo "python-3.11.7" > runtime.txt

# Create .env.example for reference
echo "📝 Creating .env.example..."
cat > .env.example << 'ENV'
# Flask Configuration
SECRET_KEY=change-this-to-random-secret-key
FLASK_ENV=production

# API Keys (add your real keys in Railway dashboard)
YOUTUBE_API_KEY=your_youtube_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
NEWS_API_KEY=your_news_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENV

# Create .gitignore
echo "📝 Creating .gitignore..."
cat > .gitignore << 'IGNORE'
# Environment
.env
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Database
*.db
*.sqlite
instance/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log

# Testing
test_screenshots/
test_screenshots_deep/
*.json

# OS
.DS_Store
Thumbs.db
IGNORE

# Commit changes
echo "💾 Committing deployment files..."
git add Procfile requirements.txt runtime.txt .env.example .gitignore
git commit -m "Add Railway deployment configuration"

echo ""
echo "✅ Railway deployment preparation complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Create a GitHub repository"
echo "2. Push code: git remote add origin <your-repo-url>"
echo "3. git push -u origin main"
echo "4. Go to railway.app"
echo "5. Click 'New Project' → 'Deploy from GitHub'"
echo "6. Select your repository"
echo "7. Add environment variables from .env.example"
echo "8. Deploy!"
echo ""
echo "🌐 Your app will be live at: https://your-app.railway.app"
