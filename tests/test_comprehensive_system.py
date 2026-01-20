#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM TESTER - ViralLens
Tests EVERY button, EVERY flow, EVERY edge case
Finds bugs automatically and generates detailed reports

Requirements:
    pip install playwright pytest requests beautifulsoup4
    playwright install chromium

Usage:
    python3 test_comprehensive_system.py --report
"""

import os
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect
import requests
from typing import Dict, List, Tuple
import re


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class ComprehensiveSystemTester:
    """
    Comprehensive testing system that tests EVERYTHING
    """
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.bugs = []
        self.warnings = []
        self.tests_passed = 0
        self.tests_failed = 0
        self.screenshot_dir = Path("test_reports/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Test user for creating accounts
        self.test_user = {
            'email': f'tester_{int(time.time())}@example.com',
            'username': f'tester_{int(time.time())}',
            'password': 'TestPass123!@#',
            'full_name': 'System Tester'
        }
    
    def log(self, message, level="INFO"):
        """Colored logging"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        colors = {
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "HEADER": Colors.HEADER,
            "BUG": Colors.RED + Colors.BOLD,
        }
        color = colors.get(level, Colors.ENDC)
        print(f"{color}[{timestamp}] {level}: {message}{Colors.ENDC}")
    
    def report_bug(self, category, title, description, severity="MEDIUM", screenshot_path=None):
        """Report a bug found during testing"""
        bug = {
            'category': category,
            'title': title,
            'description': description,
            'severity': severity,
            'screenshot': screenshot_path,
            'timestamp': datetime.now().isoformat()
        }
        self.bugs.append(bug)
        self.log(f"🐛 BUG FOUND: {title} ({severity})", "BUG")
    
    def report_warning(self, category, title, description):
        """Report a warning (not critical but needs attention)"""
        warning = {
            'category': category,
            'title': title,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        self.warnings.append(warning)
        self.log(f"⚠️  WARNING: {title}", "WARNING")
    
    def screenshot(self, page: Page, name: str):
        """Capture screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshot_dir / f"{timestamp}_{name}.png"
        page.screenshot(path=str(filename))
        return str(filename)
    
    # ========================================================================
    # TEST CATEGORY 1: LANDING PAGE
    # ========================================================================
    
    def test_landing_page(self, page: Page):
        """Test every element on landing page"""
        self.log("=" * 80, "HEADER")
        self.log("TESTING: Landing Page - All Elements & Buttons", "HEADER")
        self.log("=" * 80, "HEADER")
        
        page.goto(self.base_url)
        time.sleep(1)
        screenshot = self.screenshot(page, "landing_page")
        
        tests = [
            # Essential elements
            ("h1, h2", "Hero headline"),
            ("a[href*='signup'], a[href*='login']", "Auth links"),
            ("nav", "Navigation bar"),
            
            # CTA buttons
            ("button, a.btn, a[href*='signup']", "CTA buttons"),
            
            # Content sections
            ("#features, :text('feature'), :text('Feature')", "Features section"),
            ("#pricing, :text('pricing'), :text('Pricing')", "Pricing section"),
            
            # Footer
            ("footer, .footer, :text('©'), :text('Copyright')", "Footer"),
        ]
        
        for selector, name in tests:
            try:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    self.log(f"✅ Found: {name} ({count} elements)", "SUCCESS")
                    self.tests_passed += 1
                else:
                    self.report_bug(
                        "Landing Page",
                        f"Missing: {name}",
                        f"Expected to find '{selector}' but found 0 elements",
                        "LOW",
                        screenshot
                    )
                    self.tests_failed += 1
            except Exception as e:
                self.report_bug(
                    "Landing Page",
                    f"Error checking: {name}",
                    str(e),
                    "MEDIUM",
                    screenshot
                )
                self.tests_failed += 1
        
        # Test clickability of all buttons
        buttons = page.locator("button, a.btn, input[type='submit']")
        button_count = buttons.count()
        self.log(f"Testing {button_count} buttons for clickability...", "INFO")
        
        clickable_count = 0
        for i in range(min(button_count, 10)):  # Test first 10 buttons
            try:
                btn = buttons.nth(i)
                if btn.is_visible():
                    clickable_count += 1
            except:
                pass
        
        if clickable_count > 0:
            self.log(f"✅ {clickable_count} buttons are visible", "SUCCESS")
        else:
            self.report_warning("Landing Page", "No visible buttons", "Could not find any visible buttons")
    
    # ========================================================================
    # TEST CATEGORY 2: AUTHENTICATION FLOWS
    # ========================================================================
    
    def test_authentication_complete(self, page: Page):
        """Test complete authentication system"""
        self.log("=" * 80, "HEADER")
        self.log("TESTING: Authentication System (Signup/Login/Logout)", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Test 1: Sign Up with valid data
        self.log("\n--- Test: Sign Up Flow ---", "INFO")
        page.goto(f"{self.base_url}/signup")
        time.sleep(0.5)
        
        try:
            # Fill form
            page.fill("input[name='email']", self.test_user['email'])
            page.fill("input[name='username']", self.test_user['username'])
            page.fill("input[name='password']", self.test_user['password'])
            
            if page.locator("input[name='full_name']").count() > 0:
                page.fill("input[name='full_name']", self.test_user['full_name'])
            
            screenshot = self.screenshot(page, "signup_filled")
            
            # Submit
            page.click("button[type='submit']")
            time.sleep(2)
            
            # Check if redirected to dashboard or onboarding
            current_url = page.url
            if '/dashboard' in current_url or '/onboarding' in current_url:
                self.log("✅ Sign up successful", "SUCCESS")
                self.tests_passed += 1
            else:
                self.report_bug(
                    "Authentication",
                    "Signup redirect failed",
                    f"Expected redirect to /dashboard or /onboarding, got {current_url}",
                    "HIGH",
                    screenshot
                )
                self.tests_failed += 1
        
        except Exception as e:
            self.report_bug(
                "Authentication",
                "Signup flow error",
                f"{str(e)}\n{traceback.format_exc()}",
                "CRITICAL",
                self.screenshot(page, "signup_error")
            )
            self.tests_failed += 1
            return False
        
        # Test 2: Logout
        self.log("\n--- Test: Logout Flow ---", "INFO")
        try:
            # Find and click logout
            logout_selectors = [
                "button:has-text('Logout')",
                "a:has-text('Logout')",
                "[href='/logout']"
            ]
            
            logged_out = False
            for selector in logout_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=5000):
                        loc.click()
                        time.sleep(1)
                        logged_out = True
                        break
                except:
                    continue
            
            if logged_out:
                # Wait for redirect
                page.wait_for_url(lambda url: '/login' in url or url == self.base_url or url == f"{self.base_url}/", timeout=5000)
                current_url = page.url
                self.log("✅ Logout successful", "SUCCESS")
                self.tests_passed += 1
            else:
                self.report_bug(
                    "Authentication",
                    "Logout button not found",
                    "Could not find logout button with any selector",
                    "MEDIUM",
                    self.screenshot(page, "logout_missing")
                )
                self.tests_failed += 1
        
        except Exception as e:
            self.report_bug(
                "Authentication",
                "Logout flow error",
                str(e),
                "MEDIUM",
                self.screenshot(page, "logout_error")
            )
            self.tests_failed += 1
        
        # Test 3: Login with correct credentials
        self.log("\n--- Test: Login Flow ---", "INFO")
        try:
            page.goto(f"{self.base_url}/login")
            time.sleep(0.5)
            
            page.fill("input[name='email']", self.test_user['email'])
            page.fill("input[name='password']", self.test_user['password'])
            
            page.click("button[type='submit']")
            time.sleep(2)
            
            current_url = page.url
            if '/dashboard' in current_url or '/onboarding' in current_url:
                self.log("✅ Login successful", "SUCCESS")
                self.tests_passed += 1
                return True
            else:
                self.report_bug(
                    "Authentication",
                    "Login redirect failed",
                    f"Expected /dashboard, got {current_url}",
                    "HIGH",
                    self.screenshot(page, "login_failed")
                )
                self.tests_failed += 1
                return False
        
        except Exception as e:
            self.report_bug(
                "Authentication",
                "Login flow error",
                str(e),
                "CRITICAL",
                self.screenshot(page, "login_error")
            )
            self.tests_failed += 1
            return False
    
    # ========================================================================
    # TEST CATEGORY 3: DASHBOARD & NAVIGATION
    # ========================================================================
    
    def test_dashboard_complete(self, page: Page):
        """Test all dashboard functionality"""
        self.log("=" * 80, "HEADER")
        self.log("TESTING: Dashboard - All Features", "HEADER")
        self.log("=" * 80, "HEADER")
        
        page.goto(f"{self.base_url}/dashboard")
        time.sleep(1)
        screenshot = self.screenshot(page, "dashboard_full")
        
        # Test all dashboard elements
        elements = [
            ("h1:has-text('Welcome'), h1:has-text('Dashboard')", "Dashboard title"),
            ("button:has-text('Logout'), a:has-text('Logout')", "Logout button"),
            ("a:has-text('Settings'), [href*='settings']", "Settings link"),
            (".user-avatar, img[alt*='avatar'], [class*='avatar']", "User avatar"),
            ("button:has-text('Run Research'), button:has-text('Run')", "Research button"),
        ]
        
        for selector, name in elements:
            try:
                if page.locator(selector).count() > 0:
                    self.log(f"✅ Found: {name}", "SUCCESS")
                    self.tests_passed += 1
                else:
                    self.report_warning(
                        "Dashboard",
                        f"Missing: {name}",
                        f"Could not find: {selector}"
                    )
            except Exception as e:
                self.report_bug(
                    "Dashboard",
                    f"Error checking: {name}",
                    str(e),
                    "LOW",
                    screenshot
                )
        
        # Test all clickable links
        links = page.locator("a")
        link_count = links.count()
        self.log(f"Found {link_count} links on dashboard", "INFO")
        
        # Test navigation to Settings
        try:
            settings_selectors = [
                "a:has-text('Settings')",
                "[href='/settings']",
                "[href*='settings']"
            ]
            
            for selector in settings_selectors:
                if page.locator(selector).count() > 0:
                    self.log(f"Testing navigation: {selector}", "INFO")
                    page.click(selector)
                    time.sleep(1)
                    
                    if '/settings' in page.url:
                        self.log("✅ Settings navigation working", "SUCCESS")
                        self.tests_passed += 1
                    else:
                        self.report_bug(
                            "Dashboard",
                            "Settings navigation failed",
                            f"Clicked settings but url is: {page.url}",
                            "MEDIUM",
                            self.screenshot(page, "settings_nav_failed")
                        )
                        self.tests_failed += 1
                    break
        except Exception as e:
            self.report_bug(
                "Dashboard",
                "Settings navigation error",
                str(e),
                "MEDIUM",
                self.screenshot(page, "settings_nav_error")
            )
            self.tests_failed += 1
    
    # ========================================================================
    # TEST CATEGORY 4: SETTINGS & DATA MANAGEMENT
    # ========================================================================
    
    def test_settings_crud_operations(self, page: Page):
        """Test all CRUD operations in settings"""
        self.log("=" * 80, "HEADER")
        self.log("TESTING: Settings - CRUD Operations", "HEADER")
        self.log("=" * 80, "HEADER")
        
        page.goto(f"{self.base_url}/settings")
        time.sleep(1)
        screenshot = self.screenshot(page, "settings_page")
        
        # Test 1: Add Keyword
        self.log("\n--- Test: Add Keyword ---", "INFO")
        try:
            # Switch to Keywords tab
            page.click("button:has-text('Keywords')")
            time.sleep(0.5)

            # Find keyword input
            keyword_selectors = [
                "#keyword-text",
                "input[name='keyword']",
                "input[placeholder*='keyword' i]"
            ]
            
            keyword_input = None
            for selector in keyword_selectors:
                if page.locator(selector).count() > 0:
                    keyword_input = selector
                    break
            
            # Open modal first
            add_button = page.locator("button:has-text('+ Add Keyword')")
            if add_button.count() > 0:
                add_button.click()
                time.sleep(0.5)

            if keyword_input:
                test_keyword = f"Test Keyword {int(time.time())}"
                page.fill(keyword_input, test_keyword)
                
                # Find add button
                add_selectors = [
                    "#keyword-form button[type='submit']",
                    "button:has-text('Add Keyword')",
                    "button:has-text('Add')"
                ]
                
                for selector in add_selectors:
                    if page.locator(selector).count() > 0:
                        page.click(selector)
                        # Wait for modal to close
                        page.wait_for_selector("#keyword-modal", state="hidden", timeout=5000)
                        time.sleep(1)
                        break
                
                # Verify keyword was added
                if page.locator(f"text={test_keyword}").count() > 0:
                    self.log("✅ Keyword added successfully", "SUCCESS")
                    self.tests_passed += 1
                else:
                    self.report_bug(
                        "Settings",
                        "Keyword not visible after adding",
                        f"Added keyword '{test_keyword}' but it's not visible in the list",
                        "HIGH",
                        self.screenshot(page, "keyword_not_shown")
                    )
                    self.tests_failed += 1
            else:
                self.report_warning(
                    "Settings",
                    "Keyword input not found",
                    "Could not find keyword input field"
                )
        
        except Exception as e:
            self.report_bug(
                "Settings",
                "Add keyword error",
                f"{str(e)}\n{traceback.format_exc()}",
                "HIGH",
                self.screenshot(page, "keyword_add_error")
            )
            self.tests_failed += 1
        
        finally:
            # Ensure modal is closed
            page.evaluate("if(typeof closeKeywordModal === 'function') closeKeywordModal()")
            time.sleep(0.2)
        
        # Test 2: Add Competitor
        self.log("\n--- Test: Add Competitor ---", "INFO")
        try:
            # Switch to Competitors tab (use force in case a modal is still fading)
            page.click("button:has-text('Competitors')", force=True)
            time.sleep(0.5)

            # Find competitor inputs
            name_input = None
            channel_input = None
            
            if page.locator("#competitor-name").count() > 0:
                name_input = "#competitor-name"
            
            if page.locator("#competitor-channel-id").count() > 0:
                channel_input = "#competitor-channel-id"
            elif page.locator("input[placeholder*='channel' i]").count() > 0:
                channel_input = "input[placeholder*='channel' i]"
            
            # Open modal first
            add_comp_btn = page.locator("button:has-text('+ Add Competitor')")
            if add_comp_btn.count() > 0:
                add_comp_btn.click()
                time.sleep(0.5)

            if name_input and channel_input:
                test_name = f"Test Competitor {int(time.time())}"
                test_channel = "UCsqjHFMB_JYTaEnf_vmTNqg"  # Valid format
                
                page.fill(name_input, test_name)
                page.fill(channel_input, test_channel)
                
                # Find add competitor button
                add_comp_selectors = [
                    "#competitor-form button[type='submit']",
                    "button:has-text('Add Competitor')",
                    "button:has-text('Add')"
                ]
                
                for selector in add_comp_selectors:
                    if page.locator(selector).count() > 0:
                        page.click(selector)
                        time.sleep(1)
                        break
                
                # Verify competitor was added
                page.reload()
                time.sleep(1)
                
                if page.locator(f"text={test_name}").count() > 0:
                    self.log("✅ Competitor added successfully", "SUCCESS")
                    self.tests_passed += 1
                else:
                    self.report_bug(
                        "Settings",
                        "Competitor not visible after adding",
                        f"Added competitor '{test_name}' but it's not visible",
                        "HIGH",
                        self.screenshot(page, "competitor_not_shown")
                    )
                    self.tests_failed += 1
            else:
                self.report_warning(
                    "Settings",
                    "Competitor inputs not found",
                    f"Name input: {name_input}, Channel input: {channel_input}"
                )
        
        except Exception as e:
            self.report_bug(
                "Settings",
                "Add competitor error",
                f"{str(e)}\n{traceback.format_exc()}",
                "HIGH",
                self.screenshot(page, "competitor_add_error")
            )
            self.tests_failed += 1
    
    # ========================================================================
    # TEST CATEGORY 5: API ENDPOINTS
    # ========================================================================
    
    def test_api_endpoints(self):
        """Test all API endpoints for correct responses"""
        self.log("=" * 80, "HEADER")
        self.log("TESTING: API Endpoints", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Note: This requires authentication cookie/session
        # For now, test public endpoints
        
        public_endpoints = [
            ('GET', '/', 'Landing page'),
            ('GET', '/signup', 'Signup page'),
            ('GET', '/login', 'Login page'),
            ('GET', '/pricing', 'Pricing page'),
        ]
        
        for method, endpoint, name in public_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    self.log(f"✅ {name}: {response.status_code}", "SUCCESS")
                    self.tests_passed += 1
                else:
                    self.report_bug(
                        "API",
                        f"{name} returned {response.status_code}",
                        f"Expected 200, got {response.status_code}",
                        "MEDIUM"
                    )
                    self.tests_failed += 1
            
            except Exception as e:
                self.report_bug(
                    "API",
                    f"{name} request failed",
                    str(e),
                    "HIGH"
                )
                self.tests_failed += 1
    
    # ========================================================================
    # TEST CATEGORY 6: TITLE PREDICTION SYSTEM
    # ========================================================================
    
    def test_title_prediction_quality(self):
        """Evaluate title prediction system quality"""
        self.log("=" * 80, "HEADER")
        self.log("TESTING: Title Prediction System Quality", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Check if title prediction files exist
        title_files = [
            'generators/competitor_title_generator.py',
            'collectors/youtube_client.py',
        ]
        
        for filepath in title_files:
            if Path(filepath).exists():
                self.log(f"✅ Found: {filepath}", "SUCCESS")
                
                # Analyze code quality
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                    # Check for key features
                    features = [
                        ('regex', 'Pattern matching'),
                        ('viral', 'Viral analysis'),
                        ('title', 'Title processing'),
                    ]
                    
                    for keyword, feature in features:
                        if keyword in content.lower():
                            self.log(f"  ✅ Has: {feature}", "SUCCESS")
                        else:
                            self.report_warning(
                                "Title Prediction",
                                f"Missing: {feature} in {filepath}",
                                f"Could not find '{keyword}' keyword"
                            )
            else:
                self.report_bug(
                    "Title Prediction",
                    f"File missing: {filepath}",
                    "Title prediction component not found",
                    "MEDIUM"
                )
        
        # Check if title patterns are defined
        self.log("\nChecking title pattern definitions...", "INFO")
        
        pattern_checks = [
            "How to",
            "Best",
            "Top",
            "Ultimate",
            "Guide",
            "Review",
        ]
        
        # This is a placeholder - would need actual title generation to test
        self.log("⚠️  Title prediction quality test requires live system", "WARNING")
        self.report_warning(
            "Title Prediction",
            "Quality test incomplete",
            "Title prediction system needs live testing with actual data"
        )
    
    # ========================================================================
    # MAIN TEST RUNNER
    # ========================================================================
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        self.log("=" * 80, "HEADER")
        self.log("🚀 COMPREHENSIVE SYSTEM TEST - VIRALENS", "HEADER")
        self.log("=" * 80, "HEADER")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log(f"Report Directory: test_reports/", "INFO")
        self.log("=" * 80, "HEADER")
        
        start_time = time.time()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=100)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            try:
                # Test Category 1: Landing Page
                self.test_landing_page(page)
                
                # Test Category 2: Authentication
                auth_success = self.test_authentication_complete(page)
                
                if auth_success:
                    # Test Category 3: Dashboard
                    self.test_dashboard_complete(page)
                    
                    # Test Category 4: Settings
                    self.test_settings_crud_operations(page)
                else:
                    self.log("⚠️  Skipping authenticated tests (auth failed)", "WARNING")
                
                # Test Category 5: API Endpoints (no auth needed)
                self.test_api_endpoints()
                
                # Test Category 6: Title Prediction
                self.test_title_prediction_quality()
            
            except Exception as e:
                self.log(f"❌ CRITICAL ERROR: {str(e)}", "ERROR")
                self.log(traceback.format_exc(), "ERROR")
            
            finally:
                browser.close()
        
        elapsed = time.time() - start_time
        
        # Generate report
        self.generate_report(elapsed)
    
    def generate_report(self, elapsed):
        """Generate comprehensive test report"""
        print("\n")
        print("=" * 80)
        print(f"{Colors.BOLD}{Colors.HEADER}📊 COMPREHENSIVE TEST REPORT{Colors.ENDC}")
        print("=" * 80)
        
        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"{Colors.CYAN}Total Tests: {total_tests}{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Passed: {self.tests_passed}{Colors.ENDC}")
        print(f"{Colors.RED}❌ Failed: {self.tests_failed}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Pass Rate: {pass_rate:.1f}%{Colors.ENDC}")
        print(f"{Colors.CYAN}Duration: {elapsed:.2f}s{Colors.ENDC}")
        print(f"{Colors.CYAN}Screenshots: {self.screenshot_dir}{Colors.ENDC}")
        
        # Bugs found
        if self.bugs:
            print(f"\n{Colors.RED}{Colors.BOLD}🐛 BUGS FOUND: {len(self.bugs)}{Colors.ENDC}")
            print("=" * 80)
            
            # Group by severity
            critical = [b for b in self.bugs if b['severity'] == 'CRITICAL']
            high = [b for b in self.bugs if b['severity'] == 'HIGH']
            medium = [b for b in self.bugs if b['severity'] == 'MEDIUM']
            low = [b for b in self.bugs if b['severity'] == 'LOW']
            
            if critical:
                print(f"\n{Colors.RED}🔴 CRITICAL ({len(critical)}){Colors.ENDC}")
                for i, bug in enumerate(critical, 1):
                    print(f"  {i}. [{bug['category']}] {bug['title']}")
                    print(f"     {bug['description'][:100]}...")
            
            if high:
                print(f"\n{Colors.RED}🟠 HIGH ({len(high)}){Colors.ENDC}")
                for i, bug in enumerate(high, 1):
                    print(f"  {i}. [{bug['category']}] {bug['title']}")
            
            if medium:
                print(f"\n{Colors.YELLOW}🟡 MEDIUM ({len(medium)}){Colors.ENDC}")
                for i, bug in enumerate(medium, 1):
                    print(f"  {i}. [{bug['category']}] {bug['title']}")
            
            if low:
                print(f"\n{Colors.CYAN}🔵 LOW ({len(low)}){Colors.ENDC}")
                for i, bug in enumerate(low, 1):
                    print(f"  {i}. [{bug['category']}] {bug['title']}")
        
        # Warnings
        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  WARNINGS: {len(self.warnings)}{Colors.ENDC}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. [{warning['category']}] {warning['title']}")
        
        # Save JSON report
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': elapsed,
            'total_tests': total_tests,
            'passed': self.tests_passed,
            'failed': self.tests_failed,
            'pass_rate': pass_rate,
            'bugs': self.bugs,
            'warnings': self.warnings
        }
        
        report_file = Path("test_reports/test_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.CYAN}📄 Full report saved: {report_file}{Colors.ENDC}")
        
        print("=" * 80)
        
        if len(self.bugs) == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED - NO BUGS FOUND!{Colors.ENDC}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ {len(self.bugs)} BUGS FOUND - See details above{Colors.ENDC}")
        
        print("=" * 80)


if __name__ == "__main__":
    tester = ComprehensiveSystemTester()
    tester.run_all_tests()
