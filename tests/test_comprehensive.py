#!/usr/bin/env python3
"""
ViralLens - Comprehensive Automated Test Suite
Tests all features, data isolation, API endpoints, and edge cases
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestViralLensSystem(unittest.TestCase):
    """Comprehensive system tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
        print("  VIRALENS AUTOMATED TEST SUITE")
        print(f"{'='*70}{Colors.END}\n")
        print(f"Testing against: {BASE_URL}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Check if server is running
        try:
            response = requests.get(BASE_URL, timeout=5)
            print(f"{Colors.GREEN}✅ Server is running{Colors.END}\n")
        except requests.exceptions.RequestException:
            print(f"{Colors.RED}❌ Server is not running at {BASE_URL}{Colors.END}")
            print(f"\nPlease start the server first:")
            print(f"  cd /Users/jahanzeb/Desktop/Code/royal-research-automation")
            print(f"  python3 app.py\n")
            sys.exit(1)
    
    def setUp(self):
        """Set up before each test"""
        self.session = requests.Session()
        self.timestamp = int(time.time() * 100000)  # High precision
        
    def tearDown(self):
        """Clean up after each test"""
        self.session.close()
    
    # ============================================================================
    # AUTHENTICATION TESTS
    # ============================================================================
    
    def test_001_landing_page_accessible(self):
        """Test: Landing page loads successfully"""
        response = self.session.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ViralLens', response.content)
        print(f"{Colors.GREEN}✅ Landing page accessible{Colors.END}")
    
    def test_002_signup_with_valid_data(self):
        """Test: User can sign up with valid credentials"""
        data = {
            'email': f'test_{self.timestamp}@example.com',
            'username': f'testuser_{self.timestamp}',
            'password': 'ValidPass123!',
            'full_name': 'Test User',
            'niche': 'automotive'
        }
        
        response = self.session.post(f"{BASE_URL}/signup", data=data, allow_redirects=False)
        self.assertIn(response.status_code, [200, 302, 303])
        print(f"{Colors.GREEN}✅ Signup successful{Colors.END}")
    
    def test_003_signup_with_duplicate_email(self):
        """Test: Cannot sign up with duplicate email"""
        email = f'duplicate_{self.timestamp}@example.com'
        
        # First signup
        data1 = {
            'email': email,
            'username': f'user1_{self.timestamp}',
            'password': 'Pass123!',
            'full_name': 'User One'
        }
        self.session.post(f"{BASE_URL}/signup", data=data1)
        
        # Second signup with same email (use fresh session)
        data2 = {
            'email': email,
            'username': f'user2_{self.timestamp}',
            'password': 'Pass456!',
            'full_name': 'User Two'
        }
        # Use new session to simulate different user (otherwise redirects to dashboard)
        session2 = requests.Session()
        response = session2.post(f"{BASE_URL}/signup", data=data2)
        # Check for new flash message
        # Check for new flash message (or JSON error if test used JSON, but here used form)
        self.assertIn(b'email already registered', response.content.lower())
        print(f"{Colors.GREEN}✅ Duplicate email rejected{Colors.END}")

    def test_004_login_with_valid_credentials(self):
        """Test: User can login with correct credentials"""
        # Create user
        email = f'login_test_{self.timestamp}@example.com'
        password = 'ValidPass123!'
        
        signup_data = {
            'email': email,
            'username': f'loginuser_{self.timestamp}',
            'password': password,
            'full_name': 'Login Test User'
        }
        self.session.post(f"{BASE_URL}/signup", data=signup_data)
        
        # Logout first
        self.session.get(f"{BASE_URL}/logout")
        
        # Try to login
        login_data = {'email': email, 'password': password}
        response = self.session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        self.assertIn(response.status_code, [200, 302, 303])
        print(f"{Colors.GREEN}✅ Login successful{Colors.END}")

    def test_005_login_with_invalid_credentials(self):
        """Test: Cannot login with wrong password"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'WrongPassword123!'
        }
        response = self.session.post(f"{BASE_URL}/login", data=login_data)
        # Check for flash message in HTML
        if b'invalid email or password' not in response.content.lower():
             print(f"{Colors.RED}DEBUG: Response content: {response.content[:500]}...{Colors.END}")
        self.assertIn(b'invalid email or password', response.content.lower())
        print(f"{Colors.GREEN}✅ Invalid credentials rejected{Colors.END}")
    
    def test_006_protected_routes_require_login(self):
        """Test: Dashboard requires authentication"""
        # Create new session (not logged in)
        session = requests.Session()
        response = session.get(f"{BASE_URL}/dashboard", allow_redirects=False)
        self.assertIn(response.status_code, [302, 303, 401])
        print(f"{Colors.GREEN}✅ Protected routes require login{Colors.END}")
    
    def test_007_logout_functionality(self):
        """Test: User can logout successfully"""
        # Login first
        self._create_and_login_user()
        
        # Logout
        response = self.session.get(f"{BASE_URL}/logout", allow_redirects=False)
        self.assertIn(response.status_code, [200, 302, 303])
        
        # Verify can't access protected route
        response = self.session.get(f"{BASE_URL}/dashboard", allow_redirects=False)
        self.assertIn(response.status_code, [302, 303, 401])
        print(f"{Colors.GREEN}✅ Logout clears session{Colors.END}")
    
    # ============================================================================
    # KEYWORD MANAGEMENT TESTS
    # ============================================================================
    
    def test_101_add_keyword(self):
        """Test: Can add keyword via API"""
        self._create_and_login_user()
        
        keyword_data = {
            'keyword': 'Test keyword for automation',
            'category': 'primary'
        }
        
        response = self.session.post(f"{BASE_URL}/api/keywords", json=keyword_data)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        print(f"{Colors.GREEN}✅ Keyword added successfully{Colors.END}")
    
    def test_102_get_keywords(self):
        """Test: Can retrieve keywords for logged-in user"""
        self._create_and_login_user()
        
        # Add a keyword first
        self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'Retrievable keyword',
            'category': 'primary'
        })
        
        # Get keywords
        response = self.session.get(f"{BASE_URL}/api/keywords")
        self.assertEqual(response.status_code, 200)
        
        keywords = response.json()
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        print(f"{Colors.GREEN}✅ Keywords retrieved successfully{Colors.END}")
    
    def test_103_edit_keyword(self):
        """Test: Can edit existing keyword"""
        self._create_and_login_user()
        
        # Add keyword
        add_response = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'Original keyword',
            'category': 'primary'
        })
        keyword_id = add_response.json().get('keyword', {}).get('id')
        
        # Edit keyword
        edit_response = self.session.put(f"{BASE_URL}/api/keywords/{keyword_id}", json={
            'keyword': 'Updated keyword',
            'category': 'secondary'
        })
        self.assertEqual(edit_response.status_code, 200)
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/keywords")
        keywords = get_response.json()
        updated = next((k for k in keywords if k['id'] == keyword_id), None)
        self.assertIsNotNone(updated)
        self.assertEqual(updated['keyword'], 'Updated keyword')
        self.assertEqual(updated['category'], 'secondary')
        print(f"{Colors.GREEN}✅ Keyword edited successfully{Colors.END}")
    
    def test_104_toggle_keyword(self):
        """Test: Can toggle keyword enable/disable"""
        self._create_and_login_user()
        
        # Add keyword
        add_response = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'Toggle test keyword',
            'category': 'primary'
        })
        keyword_id = add_response.json().get('keyword', {}).get('id')
        
        # Get initial state
        get_response = self.session.get(f"{BASE_URL}/api/keywords")
        keywords = get_response.json()
        keyword = next((k for k in keywords if k['id'] == keyword_id), None)
        original_state = keyword['enabled']
        
        # Toggle
        toggle_response = self.session.post(f"{BASE_URL}/api/keywords/{keyword_id}/toggle")
        self.assertEqual(toggle_response.status_code, 200)
        
        # Verify state changed
        get_response = self.session.get(f"{BASE_URL}/api/keywords")
        keywords = get_response.json()
        keyword = next((k for k in keywords if k['id'] == keyword_id), None)
        self.assertNotEqual(keyword['enabled'], original_state)
        print(f"{Colors.GREEN}✅ Keyword toggled successfully{Colors.END}")
    
    def test_105_delete_keyword(self):
        """Test: Can delete keyword"""
        self._create_and_login_user()
        
        # Add keyword
        add_response = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'Keyword to delete',
            'category': 'primary'
        })
        keyword_id = add_response.json().get('keyword', {}).get('id')
        
        # Delete keyword
        delete_response = self.session.delete(f"{BASE_URL}/api/keywords/{keyword_id}")
        self.assertEqual(delete_response.status_code, 200)
        
        # Verify deleted
        get_response = self.session.get(f"{BASE_URL}/api/keywords")
        keywords = get_response.json()
        deleted = next((k for k in keywords if k['id'] == keyword_id), None)
        self.assertIsNone(deleted)
        print(f"{Colors.GREEN}✅ Keyword deleted successfully{Colors.END}")
    
    def test_106_keyword_category_field(self):
        """Test: Keyword category field is saved correctly"""
        self._create_and_login_user()
        
        # Add primary keyword
        response1 = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'Primary test',
            'category': 'primary'
        })
        id1 = response1.json().get('keyword', {}).get('id')
        
        # Add secondary keyword
        response2 = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'Secondary test',
            'category': 'secondary'
        })
        id2 = response2.json().get('keyword', {}).get('id')
        
        # Verify categories
        get_response = self.session.get(f"{BASE_URL}/api/keywords")
        keywords = get_response.json()
        
        kw1 = next((k for k in keywords if k['id'] == id1), None)
        kw2 = next((k for k in keywords if k['id'] == id2), None)
        
        self.assertEqual(kw1['category'], 'primary')
        self.assertEqual(kw2['category'], 'secondary')
        print(f"{Colors.GREEN}✅ Keyword categories saved correctly{Colors.END}")
    
    # ============================================================================
    # COMPETITOR MANAGEMENT TESTS
    # ============================================================================
    
    def test_201_add_competitor(self):
        """Test: Can add competitor via API"""
        self._create_and_login_user()
        
        competitor_data = {
            'name': 'Test Competitor',
            'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg',
            'url': 'https://www.youtube.com/@testchannel',
            'description': 'Test description'
        }
        
        response = self.session.post(f"{BASE_URL}/api/competitors", json=competitor_data)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        print(f"{Colors.GREEN}✅ Competitor added successfully{Colors.END}")
    
    def test_202_get_competitors(self):
        """Test: Can retrieve competitors for logged-in user"""
        self._create_and_login_user()
        
        # Add a competitor first
        self.session.post(f"{BASE_URL}/api/competitors", json={
            'name': 'Retrievable Competitor',
            'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg',
            'url': 'https://www.youtube.com/@retrieve'
        })
        
        # Get competitors
        response = self.session.get(f"{BASE_URL}/api/competitors")
        self.assertEqual(response.status_code, 200)
        
        competitors = response.json()
        self.assertIsInstance(competitors, list)
        self.assertGreater(len(competitors), 0)
        print(f"{Colors.GREEN}✅ Competitors retrieved successfully{Colors.END}")
    
    def test_203_toggle_competitor(self):
        """Test: Can toggle competitor enable/disable"""
        self._create_and_login_user()
        
        # Add competitor
        add_response = self.session.post(f"{BASE_URL}/api/competitors", json={
            'name': 'Toggle Competitor',
            'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg'
        })
        comp_id = add_response.json().get('competitor', {}).get('id')
        
        # Get initial state
        get_response = self.session.get(f"{BASE_URL}/api/competitors")
        competitors = get_response.json()
        comp = next((c for c in competitors if c['id'] == comp_id), None)
        original_state = comp['enabled']
        
        # Toggle
        toggle_response = self.session.post(f"{BASE_URL}/api/competitors/{comp_id}/toggle")
        self.assertEqual(toggle_response.status_code, 200)
        
        # Verify state changed
        get_response = self.session.get(f"{BASE_URL}/api/competitors")
        competitors = get_response.json()
        comp = next((c for c in competitors if c['id'] == comp_id), None)
        self.assertNotEqual(comp['enabled'], original_state)
        print(f"{Colors.GREEN}✅ Competitor toggled successfully{Colors.END}")
    
    def test_204_delete_competitor(self):
        """Test: Can delete competitor"""
        self._create_and_login_user()
        
        # Add competitor
        add_response = self.session.post(f"{BASE_URL}/api/competitors", json={
            'name': 'Delete Competitor',
            'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg'
        })
        comp_id = add_response.json().get('competitor', {}).get('id')
        
        # Delete competitor
        delete_response = self.session.delete(f"{BASE_URL}/api/competitors/{comp_id}")
        self.assertEqual(delete_response.status_code, 200)
        
        # Verify deleted
        get_response = self.session.get(f"{BASE_URL}/api/competitors")
        competitors = get_response.json()
        deleted = next((c for c in competitors if c['id'] == comp_id), None)
        self.assertIsNone(deleted)
        print(f"{Colors.GREEN}✅ Competitor deleted successfully{Colors.END}")
    
    def test_205_competitor_enabled_field(self):
        """Test: Competitor enabled field is saved correctly"""
        self._create_and_login_user()
        
        # Add competitor (should default to enabled=True)
        response = self.session.post(f"{BASE_URL}/api/competitors", json={
            'name': 'Enabled Test Competitor',
            'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg'
        })
        comp_id = response.json().get('competitor', {}).get('id')
        
        # Verify enabled=True by default
        get_response = self.session.get(f"{BASE_URL}/api/competitors")
        competitors = get_response.json()
        comp = next((c for c in competitors if c['id'] == comp_id), None)
        
        self.assertTrue(comp['enabled'])
        print(f"{Colors.GREEN}✅ Competitor enabled field correct{Colors.END}")
    
    # ============================================================================
    # DATA ISOLATION TESTS (CRITICAL)
    # ============================================================================
    
    def test_301_user_can_only_see_own_keywords(self):
        """Test: User 1 cannot see User 2's keywords"""
        # Create User 1
        user1_session = requests.Session()
        self._signup_user(user1_session, 'user1', self.timestamp)
        
        # Add keyword for User 1
        user1_session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'User 1 Keyword',
            'category': 'primary'
        })
        
        # Create User 2
        user2_session = requests.Session()
        self._signup_user(user2_session, 'user2', self.timestamp + 1)
        
        # Add keyword for User 2
        user2_session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'User 2 Keyword',
            'category': 'primary'
        })
        
        # Verify User 1 doesn't see User 2's keywords
        user1_keywords = user1_session.get(f"{BASE_URL}/api/keywords").json()
        user1_keyword_texts = [k['keyword'] for k in user1_keywords]
        self.assertIn('User 1 Keyword', user1_keyword_texts)
        self.assertNotIn('User 2 Keyword', user1_keyword_texts)
        
        # Verify User 2 doesn't see User 1's keywords
        user2_keywords = user2_session.get(f"{BASE_URL}/api/keywords").json()
        user2_keyword_texts = [k['keyword'] for k in user2_keywords]
        self.assertIn('User 2 Keyword', user2_keyword_texts)
        self.assertNotIn('User 1 Keyword', user2_keyword_texts)
        
        print(f"{Colors.GREEN}✅ Keyword isolation verified{Colors.END}")
    
    def test_302_user_can_only_see_own_competitors(self):
        """Test: User 1 cannot see User 2's competitors"""
        # Create User 1
        user1_session = requests.Session()
        self._signup_user(user1_session, 'user1_comp', self.timestamp)
        
        # Add competitor for User 1
        user1_session.post(f"{BASE_URL}/api/competitors", json={
            'name': 'User 1 Competitor',
            'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg'
        })
        
        # Create User 2
        user2_session = requests.Session()
        self._signup_user(user2_session, 'user2_comp', self.timestamp + 1)
        
        # Add competitor for User 2
        user2_session.post(f"{BASE_URL}/api/competitors", json={
            'name': 'User 2 Competitor',
            'channel_id': 'UCsqjHFMB_JYTaEnf_vmTNqg'
        })
        
        # Verify User 1 doesn't see User 2's competitors
        user1_comps = user1_session.get(f"{BASE_URL}/api/competitors").json()
        user1_comp_names = [c['name'] for c in user1_comps]
        self.assertIn('User 1 Competitor', user1_comp_names)
        self.assertNotIn('User 2 Competitor', user1_comp_names)
        
        # Verify User 2 doesn't see User 1's competitors
        user2_comps = user2_session.get(f"{BASE_URL}/api/competitors").json()
        user2_comp_names = [c['name'] for c in user2_comps]
        self.assertIn('User 2 Competitor', user2_comp_names)
        self.assertNotIn('User 1 Competitor', user2_comp_names)
        
        print(f"{Colors.GREEN}✅ Competitor isolation verified{Colors.END}")
    
    def test_303_user_cannot_delete_others_keywords(self):
        """Test: User 1 cannot delete User 2's keywords"""
        # Create User 1 and add keyword
        user1_session = requests.Session()
        self._signup_user(user1_session, 'user1_del', self.timestamp)
        user1_response = user1_session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'User 1 Protected Keyword',
            'category': 'primary'
        })
        user1_keyword_id = user1_response.json().get('keyword', {}).get('id')
        
        # Create User 2
        user2_session = requests.Session()
        self._signup_user(user2_session, 'user2_del', self.timestamp + 1)
        
        # User 2 tries to delete User 1's keyword
        delete_response = user2_session.delete(f"{BASE_URL}/api/keywords/{user1_keyword_id}")
        self.assertEqual(delete_response.status_code, 404)  # Should get 404 (not found for this user)
        
        # Verify User 1's keyword still exists
        user1_keywords = user1_session.get(f"{BASE_URL}/api/keywords").json()
        exists = any(k['id'] == user1_keyword_id for k in user1_keywords)
        self.assertTrue(exists)
        
        print(f"{Colors.GREEN}✅ Cross-user deletion blocked{Colors.END}")
    
    def test_304_user_cannot_toggle_others_competitors(self):
        """Test: User 1 cannot toggle User 2's competitors"""
        # Create User 1 and add competitor
        user1_session = requests.Session()
        self._signup_user(user1_session, 'user1_toggle', self.timestamp)
        user1_response = user1_session.post(f"{BASE_URL}/api/competitors", json={
            'name': 'User 1 Protected Competitor',
            'channel_id': 'UC1111PROTECTED'
        })
        user1_comp_id = user1_response.json().get('competitor', {}).get('id')
        
        # Create User 2
        user2_session = requests.Session()
        self._signup_user(user2_session, 'user2_toggle', self.timestamp + 1)
        
        # User 2 tries to toggle User 1's competitor
        toggle_response = user2_session.post(f"{BASE_URL}/api/competitors/{user1_comp_id}/toggle")
        self.assertEqual(toggle_response.status_code, 404)
        
        print(f"{Colors.GREEN}✅ Cross-user toggle blocked{Colors.END}")
    
    # ============================================================================
    # EDGE CASES & VALIDATION TESTS
    # ============================================================================
    
    def test_401_add_keyword_without_category(self):
        """Test: Adding keyword without category defaults to 'primary'"""
        self._create_and_login_user()
        
        response = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': 'No category keyword'
        })
        
        keyword_id = response.json().get('keyword', {}).get('id')
        
        # Verify defaults to primary
        get_response = self.session.get(f"{BASE_URL}/api/keywords")
        keywords = get_response.json()
        keyword = next((k for k in keywords if k['id'] == keyword_id), None)
        
        self.assertEqual(keyword['category'], 'primary')
        print(f"{Colors.GREEN}✅ Default category works{Colors.END}")
    
    def test_402_empty_keyword_rejected(self):
        """Test: Cannot add empty keyword"""
        self._create_and_login_user()
        
        response = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': '',
            'category': 'primary'
        })
        
        # Should fail validation
        self.assertNotEqual(response.status_code, 200)
        print(f"{Colors.GREEN}✅ Empty keyword rejected{Colors.END}")
    
    def test_403_very_long_keyword(self):
        """Test: Very long keywords are handled"""
        self._create_and_login_user()
        
        long_keyword = 'A' * 500  # 500 characters
        
        response = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': long_keyword,
            'category': 'primary'
        })
        
        # Should either accept or reject gracefully (not crash)
        self.assertIn(response.status_code, [200, 400, 422])
        print(f"{Colors.GREEN}✅ Long keyword handled{Colors.END}")
    
    def test_404_special_characters_in_keyword(self):
        """Test: Special characters in keywords work"""
        self._create_and_login_user()
        
        special_keyword = "Test @#$% & <script>alert('xss')</script>"
        
        response = self.session.post(f"{BASE_URL}/api/keywords", json={
            'keyword': special_keyword,
            'category': 'primary'
        })
        
        self.assertEqual(response.status_code, 201)
        
        # Verify it was saved correctly
        get_response = self.session.get(f"{BASE_URL}/api/keywords")
        keywords = get_response.json()
        exists = any(k['keyword'] == special_keyword for k in keywords)
        self.assertTrue(exists)
        
        print(f"{Colors.GREEN}✅ Special characters handled{Colors.END}")
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _create_and_login_user(self):
        """Helper: Create and login a test user"""
        email = f'testuser_{self.timestamp}@example.com'
        username = f'user_{self.timestamp}'
        password = 'TestPass123!'
        
        signup_data = {
            'email': email,
            'username': username,
            'password': password,
            'full_name': 'Test User',
            'niche': 'automotive'
        }
        
        self.session.post(f"{BASE_URL}/signup", data=signup_data)
        return email, password
    
    def _signup_user(self, session, username_prefix, timestamp):
        """Helper: Sign up a user with given session"""
        data = {
            'email': f'{username_prefix}_{timestamp}@example.com',
            'username': f'{username_prefix}_{timestamp}',
            'password': 'TestPass123!',
            'full_name': f'{username_prefix} User',
            'niche': 'automotive'
        }
        session.post(f"{BASE_URL}/signup", data=data)


def run_tests():
    """Run all tests with detailed reporting"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestViralLensSystem)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
    print("  TEST SUMMARY")
    print(f"{'='*70}{Colors.END}\n")
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures)
    errors = len(result.errors)
    
    print(f"Total Tests:  {total}")
    print(f"{Colors.GREEN}Passed:       {passed}{Colors.END}")
    if failed > 0:
        print(f"{Colors.RED}Failed:       {failed}{Colors.END}")
    if errors > 0:
        print(f"{Colors.RED}Errors:       {errors}{Colors.END}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! System is production-ready!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  Some tests failed. Review output above.{Colors.END}\n")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
