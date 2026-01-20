#!/usr/bin/env python3
"""
Unit Tests using Flask Test Client
Tests individual components in isolation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from app import app, db
from models import User, Keyword, Competitor, UserConfig

class TestFlaskApp(unittest.TestCase):
    """Unit tests for Flask application"""
    
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_homepage_loads(self):
        """Test: Homepage loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_signup_creates_user(self):
        """Test: Signup creates user in database"""
        response = self.client.post('/signup', data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123',
            'full_name': 'Test User',
            'niche': 'automotive'
        }, follow_redirects=True)
        
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, 'testuser')
    
    def test_password_hashing(self):
        """Test: Passwords are hashed, not stored plain"""
        with app.app_context():
            user = User(
                email='hash@example.com',
                username='hashuser',
                full_name='Hash User'
            )
            user.set_password('plainpassword')
            db.session.add(user)
            db.session.commit()
            
            # Password should be hashed
            self.assertNotEqual(user.password_hash, 'plainpassword')
            # Should be able to verify
            self.assertTrue(user.check_password('plainpassword'))
            self.assertFalse(user.check_password('wrongpassword'))
    
    def test_user_can_run_research(self):
        """Test: User subscription limits work"""
        with app.app_context():
            # Free user with 0 runs
            free_user = User(
                email='free@example.com',
                username='freeuser',
                subscription_tier='free',
                research_runs_this_month=0
            )
            free_user.set_password('pass')
            self.assertTrue(free_user.can_run_research())
            
            # Free user with 5 runs (limit reached)
            free_user.research_runs_this_month = 5
            self.assertFalse(free_user.can_run_research())
            
            # Pro user (unlimited)
            pro_user = User(
                email='pro@example.com',
                username='prouser',
                subscription_tier='pro',
                research_runs_this_month=100
            )
            pro_user.set_password('pass')
            self.assertTrue(pro_user.can_run_research())

if __name__ == '__main__':
    unittest.main(verbosity=2)
