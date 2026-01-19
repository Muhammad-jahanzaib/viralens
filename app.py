"""
ViralLens - Flask Application (FIXED VERSION)
Main web application with authentication, dashboard, and complete API endpoints
"""

import os
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
import logging

from models import db, User, ResearchRun, TitlePerformance, Keyword, Competitor, UserConfig
from main import ResearchOrchestrator
from utils.smart_setup import SmartSetup
from utils.research_processor import process_research_results

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///viralens.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure logging
logging.basicConfig(
    filename='app_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.DEBUG)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle JSON requests (for API testing)
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            full_name = data.get('full_name', '').strip()
            niche = data.get('niche', 'general')
        else:
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            full_name = request.form.get('full_name', '').strip()
            niche = request.form.get('niche', 'general')
        
        # Validation
        if not email or not username or not password:
            if request.is_json:
                return jsonify({'success': False, 'error': 'All fields are required'}), 400
            flash('All fields are required.', 'error')
            return render_template('auth/signup.html')
        
        if len(password) < 8:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/signup.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
            flash('Email already registered.', 'error')
             # Redirect to login if account exists (helps tests/users)
            return redirect(url_for('login'))
        
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username already taken'}), 400
            flash('Username already taken.', 'error')
            return render_template('auth/signup.html')
        
        # Create new user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            niche=niche,
            subscription_tier='free',
            # subscription_status='active', # Removed as not in original model snippet, causing errors? 
            # Re-adding based on user snippet provided models_v2, assuming they updated it.
            # But I should stick to KNOWN model fields. 
            # Original app.py lines 101-111 showed User instantiation.
            # I will use safe kwargs.
            research_runs_this_month=0,
            total_research_runs=0
        )
        # Handle fields that might not exist in old model
        if hasattr(User, 'subscription_status'):
             user.subscription_status = 'active'
        if hasattr(User, 'subscription_start'):
             user.subscription_start = datetime.utcnow()
             
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Auto-login for web requests
        if not request.is_json:
            login_user(user)
            flash(f'Welcome, {user.username}! Your account has been created.', 'success')
            return redirect(url_for('onboarding'))
        
        # JSON response for API requests
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        }), 201
    
    return render_template('auth/signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle JSON requests (for API testing)
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '')
        else:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not request.is_json:
                remember = request.form.get('remember', False) == 'on'
                login_user(user, remember=remember)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                flash(f'Welcome back, {user.username}!', 'success')
                
                # Redirect to onboarding if not completed
                if not user.onboarding_completed:
                    return redirect(url_for('onboarding'))

                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                # JSON response for API
                user.last_login = datetime.utcnow()
                db.session.commit()
                # Need to actually login_user for the session/cookie to be set for subsequent API calls in tests
                login_user(user) # KEY FIX FOR TEST SUITE
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username
                    }
                }), 200
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    recent_runs = ResearchRun.query.filter_by(user_id=current_user.id)\
        .order_by(ResearchRun.created_at.desc())\
        .limit(10)\
        .all()
    
    return render_template('dashboard.html', 
                         user=current_user,
                         recent_runs=recent_runs)


@app.route('/onboarding')
@login_required
def onboarding():
    """Onboarding wizard for new users"""
    return render_template('onboarding.html', user=current_user)


@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html', user=current_user)


@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')


# ============================================================================
# KEYWORD API ROUTES (USER-ISOLATED)
# ============================================================================

@app.route('/api/keywords', methods=['GET'])
@login_required
def get_keywords():
    """Get all keywords for current user"""
    keywords = Keyword.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': k.id,
        'keyword': k.keyword,
        'category': k.category,
        'enabled': k.enabled,
        'created_at': k.created_at.isoformat()
    } for k in keywords])


@app.route('/api/keywords', methods=['POST'])
@login_required
def add_keyword():
    """Add new keyword for current user"""
    data = request.get_json()
    app.logger.debug(f"DEBUG: add_keyword input: {data}")
    
    # Validation
    keyword_text = data.get('keyword', '').strip()
    if not keyword_text:
        return jsonify({'success': False, 'error': 'Keyword cannot be empty'}), 400
    
    if len(keyword_text) > 200:
        return jsonify({'success': False, 'error': 'Keyword too long (max 200 characters)'}), 400
    
    # Check for duplicates
    existing = Keyword.query.filter_by(
        user_id=current_user.id,
        keyword=keyword_text
    ).first()
    
    if existing:
        return jsonify({'success': False, 'error': 'Keyword already exists'}), 400
    
    # Create keyword
    keyword = Keyword(
        user_id=current_user.id,
        keyword=keyword_text,
        category=data.get('category', 'primary'),
        enabled=data.get('enabled', True)
    )
    
    db.session.add(keyword)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'keyword': {
            'id': keyword.id,
            'keyword': keyword.keyword,
            'category': keyword.category,
            'enabled': keyword.enabled
        }
    }), 201


@app.route('/api/keywords/<int:keyword_id>', methods=['PUT'])
@login_required
def update_keyword(keyword_id):
    """Update keyword (user-isolated)"""
    keyword = Keyword.query.filter_by(
        id=keyword_id,
        user_id=current_user.id
    ).first()
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'keyword' in data:
        new_text = data['keyword'].strip()
        if not new_text:
            return jsonify({'success': False, 'error': 'Keyword cannot be empty'}), 400
        keyword.keyword = new_text
    
    if 'category' in data:
        keyword.category = data['category']
    
    if 'enabled' in data:
        keyword.enabled = data['enabled']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'keyword': {
            'id': keyword.id,
            'keyword': keyword.keyword,
            'category': keyword.category,
            'enabled': keyword.enabled
        }
    })


@app.route('/api/keywords/<int:keyword_id>', methods=['DELETE'])
@login_required
def delete_keyword(keyword_id):
    """Delete keyword (user-isolated)"""
    keyword = Keyword.query.filter_by(
        id=keyword_id,
        user_id=current_user.id
    ).first()
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword not found'}), 404
    
    db.session.delete(keyword)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Keyword deleted'})


@app.route('/api/keywords/<int:keyword_id>/toggle', methods=['POST'])
@login_required
def toggle_keyword(keyword_id):
    """Toggle keyword enabled status (user-isolated)"""
    keyword = Keyword.query.filter_by(
        id=keyword_id,
        user_id=current_user.id
    ).first()
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword not found'}), 404
    
    keyword.enabled = not keyword.enabled
    db.session.commit()
    
    return jsonify({
        'success': True,
        'enabled': keyword.enabled
    })


# ============================================================================
# COMPETITOR API ROUTES (USER-ISOLATED)
# ============================================================================

@app.route('/api/competitors', methods=['GET'])
@login_required
def get_competitors():
    """Get all competitors for current user"""
    competitors = Competitor.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'channel_id': c.channel_id,
        'url': c.url,
        'description': c.description,
        'enabled': c.enabled,
        'created_at': c.created_at.isoformat()
    } for c in competitors])


import re
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY
from utils.youtube_validator import extract_channel_id_from_url, validate_youtube_channel_id, get_channel_id_help_text

def extract_channel_id(url):
    """
    Helper to extract Channel ID from URL.
    Combines Regex (fast) and API (robust) methods.
    """
    # 1. Try Regex/URL extraction first (Fast, no API quota)
    extracted_id = extract_channel_id_from_url(url)
    if extracted_id:
        return extracted_id
    
    # 2. API Search (Fallback for handles like @username)
    if not YOUTUBE_API_KEY: return None
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        handle = url.rstrip('/').split('/')[-1] # Simple fallback extraction
        if '@' in url: 
            handle_match = re.search(r"(@[\w-]+)", url)
            if handle_match:
                handle = handle_match.group(1)
            
        request = youtube.search().list(part='snippet', q=handle, type='channel', maxResults=1)
        response = request.execute()
        if response.get('items'):
            return response['items'][0]['snippet']['channelId']
    except Exception as e:
        app.logger.error(f"Failed to find channel ID via API: {e}")
    return None

@app.route('/api/competitors', methods=['POST'])
@login_required
def add_competitor():
    """Add new competitor for current user"""
    data = request.get_json()
    
    # Validation
    name = data.get('name', '').strip()
    
    # Handle channel_id safely (it might be None/null from JSON)
    channel_id = data.get('channel_id')
    if channel_id:
        channel_id = str(channel_id).strip()
    else:
        channel_id = ""
        
    url = data.get('url', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Competitor name cannot be empty'}), 400
    
    # Try to auto-detect channel ID if missing
    if not channel_id and url:
        channel_id = extract_channel_id(url)
    
    # Validate Channel ID Format
    if not channel_id:
         return jsonify({
            'success': False, 
            'error': 'YouTube Channel ID is required and could not be detected from URL',
            'help': 'Channel IDs start with "UC" followed by 22 characters. Example: UCsqjHFMB_JYTaEnf_vmTNqg'
        }), 400

    is_valid, error_msg = validate_youtube_channel_id(channel_id)
    if not is_valid:
        return jsonify({
            'success': False, 
            'error': error_msg,
            'help': 'Visit youtube.com/channel/YOUR_CHANNEL_ID to verify the correct ID'
        }), 400
    
    # Check for duplicates
    existing = Competitor.query.filter_by(
        user_id=current_user.id,
        channel_id=channel_id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'error': 'Competitor already exists'}), 400
    
    # Create competitor
    competitor = Competitor(
        user_id=current_user.id,
        name=name,
        channel_id=channel_id,
        enabled=data.get('enabled', True)
    )
    
    db.session.add(competitor)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'competitor': {
            'id': competitor.id,
            'name': competitor.name,
            'channel_id': competitor.channel_id,
            'enabled': competitor.enabled
        }
    }), 201


@app.route('/api/competitors/<int:competitor_id>', methods=['PUT'])
@login_required
def update_competitor(competitor_id):
    """Update competitor (user-isolated)"""
    competitor = Competitor.query.filter_by(
        id=competitor_id,
        user_id=current_user.id
    ).first()
    
    if not competitor:
        return jsonify({'success': False, 'error': 'Competitor not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({'success': False, 'error': 'Name cannot be empty'}), 400
        competitor.name = new_name
    
    if 'channel_id' in data:
        new_channel = data['channel_id'].strip()
        if not new_channel:
            return jsonify({'success': False, 'error': 'Channel ID cannot be empty'}), 400
        
        # Validate YouTube Channel ID format
        is_valid, error_msg = validate_youtube_channel_id(new_channel)
        if not is_valid:
            return jsonify({
                'success': False, 
                'error': error_msg
            }), 400
        
        competitor.channel_id = new_channel
    
    if 'enabled' in data:
        competitor.enabled = data['enabled']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'competitor': {
            'id': competitor.id,
            'name': competitor.name,
            'channel_id': competitor.channel_id,
            'enabled': competitor.enabled
        }
    })


@app.route('/api/youtube-channel-id-help', methods=['GET'])
def youtube_channel_id_help():
    """Get help text for finding YouTube Channel ID"""
    return jsonify({
        'success': True,
        'help_text': get_channel_id_help_text(),
        'examples': [
            {
                'channel': 'Doug DeMuro',
                'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg',
                'url': 'https://www.youtube.com/channel/UCsqjHFMB_JYTaEnf_vmTNqg'
            },
            {
                'channel': 'Louis Rossman',
                'channel_id': 'UCl2mFZoRqjw_ELax4Yisf6w',
                'url': 'https://www.youtube.com/channel/UCl2mFZoRqjw_ELax4Yisf6w'
            }
        ],
        'validation_rules': {
            'format': 'UC + 22 characters',
            'total_length': 24,
            'allowed_chars': 'Letters, numbers, dash (-), underscore (_)',
            'example': 'UCsqjHFMB_JYTaEnf_vmTNqg'
        }
    })

@app.route('/api/competitors/<int:competitor_id>', methods=['DELETE'])
@login_required
def delete_competitor(competitor_id):
    """Delete competitor (user-isolated)"""
    competitor = Competitor.query.filter_by(
        id=competitor_id,
        user_id=current_user.id
    ).first()
    
    if not competitor:
        return jsonify({'success': False, 'error': 'Competitor not found'}), 404
    
    db.session.delete(competitor)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Competitor deleted'})


@app.route('/api/competitors/<int:competitor_id>/toggle', methods=['POST'])
@login_required
def toggle_competitor(competitor_id):
    """Toggle competitor enabled status (user-isolated)"""
    competitor = Competitor.query.filter_by(
        id=competitor_id,
        user_id=current_user.id
    ).first()
    
    if not competitor:
        return jsonify({'success': False, 'error': 'Competitor not found'}), 404
    
    competitor.enabled = not competitor.enabled
    db.session.commit()
    
    return jsonify({
        'success': True,
        'enabled': competitor.enabled
    })


# ============================================================================
# RESEARCH API ROUTES
# ============================================================================

@app.route('/api/run-research', methods=['POST'])
@login_required
def api_run_research():
    """Run research automation"""
    
    # Check if user can run research
    if not current_user.can_run_research():
        return jsonify({
            'success': False,
            'error': 'Research limit reached for your subscription tier.'
        }), 403
    
    try:
        # Initialize orchestrator with user_id for data isolation
        orchestrator = ResearchOrchestrator(user_id=current_user.id)
        
        # Run research
        result = orchestrator.run_research(save_report=True)
        
        # Extract data from the new report structure (main.py)
        topics = result.get('claude_result', {}).get('topic_recommendations', [])
        keywords_used = result.get('keywords', [])
        sources_successful = len(result.get('sources_collected', []))
        runtime = result.get('runtime_seconds', 0.0)
        cost = result.get('cost_breakdown', {}).get('claude_api', 0.0)

        # Save research run to database
        research_run = ResearchRun(
            user_id=current_user.id,
            keywords=keywords_used,
            topics_generated=len(topics),
            sources_successful=sources_successful,
            runtime_seconds=runtime,
            api_cost=cost,
            topics_data=result.get('claude_result', {}), # Store full AI result
            json_report_path=result.get('paths', {}).get('json'),
            html_report_path=result.get('paths', {}).get('html')
        )
        db.session.add(research_run)
        
        # Increment user's research count
        current_user.increment_research_count()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'topics': topics,
            'metadata': {
                'keywords': keywords_used,
                'collection_summary': {
                    'successful': sources_successful,
                    'total_duration': runtime
                }
            },
            'run_id': research_run.id,
            'redirect_url': f'/research/results/{research_run.id}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    """Get or update user settings"""
    if request.method == 'GET':
        # Get user config or create default
        config = current_user.user_config
        if not config:
            config = UserConfig(user_id=current_user.id)
            db.session.add(config)
            db.session.commit()
            
        settings = {
            'niche': {
                'primary': current_user.niche,
                'description': config.niche_description or ''
            },
            'limits': {
                'max_keywords': 5 if current_user.subscription_tier == 'free' else 50,
                'max_competitors': 5 if current_user.subscription_tier == 'free' else 50,
                'research_runs_remaining': current_user.get_remaining_runs()
            },
            'preferences': {
                'research_depth': config.research_depth or 'standard',
                'auto_track': True
            }
        }
        return jsonify({'success': True, 'settings': settings})
    
    elif request.method == 'POST':
        data = request.json
        config = current_user.user_config
        if not config:
            config = UserConfig(user_id=current_user.id)
            db.session.add(config)
            
        if 'niche' in data:
            current_user.niche = data['niche'].get('primary', current_user.niche)
            config.niche_description = data['niche'].get('description', config.niche_description)
            
        if 'preferences' in data:
            config.research_depth = data['preferences'].get('research_depth', config.research_depth)
            
        db.session.commit()
        return jsonify({'success': True})




@app.route('/research/<int:run_id>')
@login_required
def view_research(run_id):
    """View detailed research results"""
    run = ResearchRun.query.filter_by(id=run_id, user_id=current_user.id).first_or_404()
    
    # Backfill logic for legacy runs (where topics_data is missing)
    if not run.topics_data or not run.json_report_path:
        try:
            # Attempt to find the file based on timestamp
            # File format: research_report_YYYY-MM-DD_HH-MM.json
            timestamp = run.created_at.strftime("%Y-%m-%d_%H-%M")
            filename = f"research_report_{timestamp}.json"
            filepath = os.path.abspath(os.path.join("data", "research_reports", filename))
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Extract topics
                topics = data.get('claude_result', {}).get('topic_recommendations', [])
                
                # Update DB
                run.topics_data = topics
                run.json_report_path = filepath
                
                # Also try HTML path
                html_filename = f"research_report_{timestamp}.html"
                html_path = os.path.abspath(os.path.join("data", "research_reports", html_filename))
                if os.path.exists(html_path):
                    run.html_report_path = html_path
                    
                db.session.commit()
                print(f"DEBUG: Backfilled data for Run #{run.id}")
                
        except Exception as e:
            print(f"DEBUG: Failed to backfill run {run.id}: {e}")
    
    # Process data for enhanced display
    enhanced_data = process_research_results(run)
    
    return render_template('research_results.html', run=run, enhanced=enhanced_data)


@app.route('/research/results/<int:run_id>')
@login_required
def research_results(run_id):
    """
    Display enhanced research results
    Shows comprehensive data visualization with scoring breakdown
    """
    # Get research run
    run = ResearchRun.query.filter_by(
        id=run_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Process results for display
    display_data = process_research_results(run)
    
    return render_template(
        'research_results.html',
        run=run,
        topics=display_data['topics'],
        metadata=display_data['metadata'],
        scoring_weights=display_data['scoring_weights'],
        methodology=display_data['methodology'],
        enhanced=display_data  # Keep this for compatibility with my previous template changes
    )


@app.route('/api/research/<int:run_id>/export')
@login_required
def export_research(run_id):
    """
    Export research data as JSON
    """
    run = ResearchRun.query.filter_by(
        id=run_id,
        user_id=current_user.id
    ).first()
    
    if not run:
        return jsonify({'error': 'Research run not found'}), 404
    
    display_data = process_research_results(run)
    
    return jsonify({
        'success': True,
        'data': display_data
    })



@app.route('/api/apply-niche-preset/<preset_id>', methods=['POST'])
@login_required
def api_apply_niche_preset(preset_id):
    """Apply a predefined configuration preset (Config + Data)"""
    
    # Define presets with CONFIG + DATA
    presets = {
        'automotive': {
            'niche': 'Automotive',
            'desc': 'Cars, racing, reviews, maintenance',
            'max_keywords': 4,
            'competitors': [
                {'name': 'Doug DeMuro', 'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg'},
                {'name': 'Carwow', 'channel_id': 'UCUhFaUpnq31m6TNX2olIOWg'},
                {'name': 'Top Gear', 'channel_id': 'UCjOl2AUblV62Im6pn0O8e2A'}
            ],
            'keywords': ['New Car Reviews 2025', 'Electric vs Gas Cars', 'Best SUV under 50k', 'Car Maintenance Tips']
        },
        'royal_family': {
            'niche': 'Royal Family',
            'desc': 'British Royal Family news and analysis',
            'max_keywords': 6,
            'competitors': [
                {'name': 'The Royal Family Channel', 'channel_id': 'UCCC0yU7U3v2rF5o4-wYx9Hw'},
                {'name': 'Sky News', 'channel_id': 'UCoMdktPbSTixAyNGwb-UYkQ'}
            ],
            'keywords': ['Royal Family Latest News', 'Prince William Updates', 'Kate Middleton News', 'Buckingham Palace Announcements']
        },
        'tech': {
            'niche': 'Technology',
            'desc': 'Consumer electronics, AI, software, gadgets',
            'max_keywords': 6,
            'competitors': [
                {'name': 'MKBHD', 'channel_id': 'UCBJycsmduvYl8bd8M9t76Ag'},
                {'name': 'Linus Tech Tips', 'channel_id': 'UCXuqSBlHAE6Xw-yeJA0Tunw'},
                {'name': 'The Verge', 'channel_id': 'UCddiUEpeqJcYeBxX1IVBKvQ'}
            ],
            'keywords': ['iPhone vs Android 2025', 'Best Laptop for Students', 'AI Tools Review', 'Smart Home Setup']
        },
        'finance': {
            'niche': 'Finance',
            'desc': 'Investing, stock market, personal finance',
            'max_keywords': 5,
            'competitors': [
                {'name': 'Graham Stephan', 'channel_id': 'UCV6KDgJskWaEckne5aPA0aQ'},
                {'name': 'Andrei Jikh', 'channel_id': 'UCGy7SkBjcIAgTiwkXEtPnYg'},
                {'name': 'The Plain Bagel', 'channel_id': 'UCFCEPr9ps9HfrSLavze55Wg'}
            ],
            'keywords': ['Stock Market Crash 2025', 'Dividend Investing Guide', 'Passive Income Ideas', 'Crypto Market Analysis']
        }
    }
    
    if preset_id not in presets:
        return jsonify({'success': False, 'error': 'Invalid preset ID'}), 400
        
    preset = presets[preset_id]
    
    try:
        # 1. Update Configuration
        config = current_user.user_config
        if not config:
            config = UserConfig(user_id=current_user.id)
            db.session.add(config)
            
        current_user.niche = preset['niche']
        config.niche_description = preset['desc']
        config.max_keywords = preset['max_keywords']
        
        # 2. Add Competitors (if not exists)
        added_comps = 0
        for comp_data in preset['competitors']:
            exists = Competitor.query.filter_by(
                user_id=current_user.id,
                channel_id=comp_data['channel_id']
            ).first()
            
            if not exists:
                new_comp = Competitor(
                    user_id=current_user.id,
                    name=comp_data['name'],
                    channel_id=comp_data['channel_id'],
                    url=f"https://www.youtube.com/channel/{comp_data['channel_id']}",
                    enabled=True
                )
                db.session.add(new_comp)
                added_comps += 1

        # 3. Add Keywords (if not exists)
        added_kws = 0
        for kw_text in preset.get('keywords', []):
            exists = Keyword.query.filter_by(
                user_id=current_user.id,
                keyword=kw_text
            ).first()
            
            if not exists:
                new_kw = Keyword(
                    user_id=current_user.id,
                    keyword=kw_text,
                    category='primary',
                    enabled=True
                )
                db.session.add(new_kw)
                added_kws += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Applied {preset['niche']} preset: Added {added_comps} competitors and {added_kws} keywords.",
            'details': {
                'competitors_added': added_comps,
                'keywords_added': added_kws
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/system-config', methods=['GET', 'PUT'])
@login_required
def api_system_config():
    """Get or update system configuration"""
    config = current_user.user_config
    if not config:
        config = UserConfig(user_id=current_user.id)
        db.session.add(config)
        db.session.commit()
        
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'config': {
                **config.to_dict(),
                'niche_config': {
                    'name': current_user.niche,
                    'description': config.niche_description
                }
            }
        })
        
    elif request.method == 'PUT':
        data = request.json
        try:
            # Handle dot notation updates
            for key, value in data.items():
                # Collection settings
                if key == 'collection_settings.max_keywords':
                    config.max_keywords = int(value)
                elif key == 'collection_settings.twitter_min_engagement':
                    config.twitter_min_engagement = int(value)
                elif key == 'collection_settings.reddit_min_upvotes':
                    config.reddit_min_upvotes = int(value)
                elif key == 'collection_settings.google_trends_fail_fast':
                    config.google_trends_fail_fast = bool(value)
                
                # Performance tuning
                elif key == 'performance_tuning.max_retry_attempts':
                    config.max_retry_attempts = int(value)
                elif key == 'performance_tuning.retry_on_rate_limit':
                    config.retry_on_rate_limit = bool(value)
                    
                # Reddit config
                elif key == 'reddit_config.auto_detect_subreddit':
                    config.auto_detect_subreddit = bool(value)
                elif key == 'reddit_config.default_subreddit':
                    config.default_subreddit = str(value)
                    
                # Niche config
                elif key == 'niche_config.name':
                    current_user.niche = str(value)
                elif key == 'niche_config.description':
                    config.niche_description = str(value)
                    
            db.session.commit()
            return jsonify({
                'success': True,
                'config': {
                    **config.to_dict(),
                    'niche_config': {
                        'name': current_user.niche,
                        'description': config.niche_description
                    }
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/track-title-performance', methods=['POST'])
@login_required
def api_track_title_performance():
    """Track title performance"""
    data = request.json
    
    performance = TitlePerformance(
        user_id=current_user.id,
        title=data.get('title'),
        pattern=data.get('pattern'),
        confidence=data.get('confidence'),
        views=data.get('views'),
        ctr=data.get('ctr'),
        avg_view_duration=data.get('avg_view_duration'),
        competitor_source=data.get('competitor_source')
    )
    
    db.session.add(performance)
    db.session.commit()
    
    return jsonify({'success': True, 'id': performance.id})


@app.route('/api/user-stats')
@login_required
def api_user_stats():
    """Get user statistics"""
    return jsonify({
        'research_runs_this_month': current_user.research_runs_this_month,
        'total_research_runs': current_user.total_research_runs,
        'subscription_tier': current_user.subscription_tier,
        'can_run_research': current_user.can_run_research()
    })



@app.route('/api/smart-setup', methods=['POST'])
@login_required
def api_smart_setup():
    """Run AI smart setup analysis"""
    data = request.json
    
    try:
        # Initialize SmartSetup with API key from environment
        setup = SmartSetup(os.environ.get('ANTHROPIC_API_KEY'))
        
        # 1. Analyze inputs
        analysis_result = setup.analyze_and_configure(data)
        
        # Check if analysis was successful
        if not analysis_result.get('success', False):
             return jsonify(analysis_result), 400
             
        # Extract the actual content
        recommendations = analysis_result.get('recommendations', {})
        
        # 2. Apply settings (pass only the content, not the wrapper)
        applied = setup.auto_apply_recommendations(recommendations, user_id=current_user.id)
        
        # 3. Mark onboarding as complete (partial)
        current_user.onboarding_completed = True
        current_user.onboarding_step = 2
        db.session.commit()
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'applied': applied
        })
        
    except Exception as e:
        app.logger.error(f"Smart setup failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/complete-onboarding', methods=['POST'])
@login_required
def api_complete_onboarding():
    """Mark onboarding as complete"""
    try:
        current_user.onboarding_completed = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize database"""
    db.create_all()
    print("✅ Database initialized!")


@app.cli.command()
def create_admin():
    """Create admin user"""
    admin = User(
        email='admin@viralens.ai',
        username='admin',
        full_name='Admin User',
        niche='general',
        subscription_tier='agency',
        subscription_status='active'
    )
    admin.set_password('admin123')  # Change this!
    
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin user created: admin@viralens.ai / admin123")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")
    
    print("🚀 Starting ViralLens on http://127.0.0.1:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
