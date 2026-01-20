"""
Database Models for ViralLens
User authentication, subscriptions, and research tracking
WITH USER-SPECIFIC DATA ISOLATION
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile
    full_name = db.Column(db.String(120))
    niche = db.Column(db.String(50))  # automotive, royal_family, tech, etc.
    
    # Subscription
    subscription_tier = db.Column(db.String(20), default='free')  # free, pro, agency
    subscription_status = db.Column(db.String(20), default='active')  # active, cancelled, expired
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    
    # Usage tracking
    research_runs_this_month = db.Column(db.Integer, default=0)
    total_research_runs = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Onboarding
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_step = db.Column(db.Integer, default=1) # Track progress

    # Relationships
    research_runs = db.relationship('ResearchRun', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    keywords = db.relationship('Keyword', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    competitors = db.relationship('Competitor', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    user_config = db.relationship('UserConfig', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password with validation"""
        import re
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[0-9]', password):
            raise ValueError("Password must contain at least one number")
            
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def can_run_research(self):
        """Check if user can run research based on subscription tier"""
        limits = {
            'free': 5,
            'pro': float('inf'),
            'agency': float('inf')
        }
        return self.research_runs_this_month < limits.get(self.subscription_tier, 5)
    
    def get_remaining_runs(self):
        """Get remaining research runs for this month"""
        limits = {
            'free': 5,
            'pro': float('inf'),
            'agency': float('inf')
        }
        limit = limits.get(self.subscription_tier, 5)
        if limit == float('inf'):
            return 'Unlimited'
        return max(0, limit - self.research_runs_this_month)
    
    def increment_runs(self):
        """Increment research run counters"""
        self.research_runs_this_month += 1
        self.total_research_runs += 1
        db.session.commit()
    
    def increment_research_count(self):
        """Increment research run counters (legacy alias)"""
        self.increment_runs()
    
    def get_data_directory(self):
        """Get user-specific data directory"""
        import os
        from pathlib import Path
        user_dir = Path(f"data/users/{self.id}")
        user_dir.mkdir(parents=True, exist_ok=True)
        return str(user_dir)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Keyword(db.Model):
    """User-specific keywords"""
    __tablename__ = 'keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    keyword = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='primary')  # primary, trending, secondary
    enabled = db.Column(db.Boolean, default=True)
    success_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Keyword {self.keyword}>'


class Competitor(db.Model):
    """User-specific competitors"""
    __tablename__ = 'competitors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    channel_id = db.Column(db.String(100))
    url = db.Column(db.String(500))
    description = db.Column(db.Text)
    enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_analyzed = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Competitor {self.name}>'


class UserConfig(db.Model):
    """User-specific system configuration"""
    __tablename__ = 'user_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Niche settings
    niche_description = db.Column(db.Text)
    research_depth = db.Column(db.String(20), default='standard')  # standard, deep, fast
    
    # Collection settings
    max_keywords = db.Column(db.Integer, default=4)
    twitter_min_engagement = db.Column(db.Integer, default=50)
    reddit_min_upvotes = db.Column(db.Integer, default=50)
    enable_newsapi = db.Column(db.Boolean, default=False)
    
    # Reddit config
    default_subreddit = db.Column(db.String(100), default='cars')
    auto_detect_subreddit = db.Column(db.Boolean, default=False)
    
    # Performance tuning
    parallel_collection_timeout = db.Column(db.Integer, default=90)
    max_retry_attempts = db.Column(db.Integer, default=1)
    retry_on_rate_limit = db.Column(db.Boolean, default=False)
    google_trends_fail_fast = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert config to dictionary"""
        return {
            'collection_settings': {
                'max_keywords': self.max_keywords,
                'twitter_min_engagement': self.twitter_min_engagement,
                'reddit_min_upvotes': self.reddit_min_upvotes,
                'enable_newsapi': self.enable_newsapi,
                'google_trends_fail_fast': self.google_trends_fail_fast
            },
            'reddit_config': {
                'auto_detect_subreddit': self.auto_detect_subreddit,
                'default_subreddit': self.default_subreddit
            },
            'performance_tuning': {
                'parallel_collection_timeout': self.parallel_collection_timeout,
                'max_retry_attempts': self.max_retry_attempts,
                'retry_on_rate_limit': self.retry_on_rate_limit
            }
        }
    
    def __repr__(self):
        return f'<UserConfig for User {self.user_id}>'


class ResearchRun(db.Model):
    """Research run tracking"""
    __tablename__ = 'research_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Run details
    keywords = db.Column(db.JSON)  # List of keywords used
    topics_generated = db.Column(db.Integer, default=0)
    sources_successful = db.Column(db.Integer, default=0)
    
    # Performance metrics
    runtime_seconds = db.Column(db.Float)
    api_cost = db.Column(db.Float)
    
    # Report paths (user-specific)
    json_report_path = db.Column(db.String(255))
    html_report_path = db.Column(db.String(255))
    
    # Topics data (store directly for quick access)
    topics_data = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ResearchRun {self.id} by User {self.user_id}>'


class TitlePerformance(db.Model):
    """Track title performance for learning"""
    __tablename__ = 'title_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Title details
    title = db.Column(db.String(255), nullable=False)
    pattern = db.Column(db.String(100))  # e.g., "{PERSON} EXPOSED: {CONSEQUENCE}"
    confidence = db.Column(db.String(20))  # HIGH, VERY HIGH
    
    # Performance metrics
    views = db.Column(db.Integer)
    ctr = db.Column(db.Float)  # Click-through rate
    avg_view_duration = db.Column(db.Float)  # Average view duration in seconds
    
    # Source
    competitor_source = db.Column(db.String(100))  # Which competitor inspired this
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TitlePerformance {self.id}: {self.title[:50]}>'
