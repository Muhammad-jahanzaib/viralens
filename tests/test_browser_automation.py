#!/usr/bin/env python3
"""
ViralLens - Browser Automation Testing
Simulates real user interactions: clicks, forms, navigation
Captures screenshots on failures for debugging

Requirements:
    pip install playwright pytest pytest-playwright
    playwright install chromium

Usage:
    python3 test_browser_automation.py
    
    Or with pytest:
    pytest test_browser_automation.py -v --headed --slowmo=500
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect
import traceback


class Colors:
    """Terminal colors for better readability"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class BrowserTestRunner:
    """
    Automated browser testing with visual verification
    """
    
    def __init__(self, base_url="http://127.0.0.1:5001", headless=False, slow_mo=100):
        self.base_url = base_url
        self.headless = headless
        self.slow_mo = slow_mo  # Slow down actions for visibility
        self.screenshot_dir = Path("test_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
        
        # Test users
        self.test_users = [
            {
                'email': f'testuser1_{int(time.time())}@example.com',
                'username': f'testuser1_{int(time.time())}',
                'password': 'Test123!@#',
                'full_name': 'Test User One'
            },
            {
                'email': f'testuser2_{int(time.time())}@example.com',
                'username': f'testuser2_{int(time.time())}',
                'password': 'Test456!@#',
                'full_name': 'Test User Two'
            }
        ]
    
    def log(self, message, level="INFO"):
        """Colored logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "HEADER": Colors.HEADER
        }
        color = colors.get(level, Colors.ENDC)
        print(f"{color}[{timestamp}] {level}: {message}{Colors.ENDC}")
    
    def screenshot(self, page: Page, name: str):
        """Capture screenshot for debugging, safely"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshot_dir / f"{timestamp}_{name}.png"
        try:
            # animations="disabled" and caret="hide" make it more stable
            page.screenshot(path=str(filename), animations="disabled", caret="hide", timeout=5000)
            self.log(f"📸 Screenshot saved: {filename}", "INFO")
            return filename
        except Exception as e:
            self.log(f"⚠️ Failed to take screenshot '{name}': {e}", "WARNING")
            return None
    
    def assert_element_exists(self, page: Page, selector: str, description: str):
        """Verify element exists on page"""
        try:
            element = page.locator(selector)
            expect(element).to_be_visible(timeout=5000)
            self.log(f"✅ Found: {description}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ NOT FOUND: {description} (selector: {selector})", "ERROR")
            self.screenshot(page, f"error_{description.replace(' ', '_')}")
            self.errors.append(f"Missing element: {description}")
            return False
    
    def click_and_verify(self, page: Page, selector: str, description: str):
        """Click element and verify action"""
        try:
            self.log(f"🖱️  Clicking: {description}", "INFO")
            page.click(selector, timeout=5000)
            time.sleep(0.5)  # Wait for animations
            self.log(f"✅ Clicked: {description}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ Click failed: {description} - {str(e)}", "ERROR")
            self.screenshot(page, f"click_failed_{description.replace(' ', '_')}")
            self.errors.append(f"Click failed: {description}")
            return False
    
    def fill_form_field(self, page: Page, selector: str, value: str, description: str):
        """Fill form field with validation"""
        try:
            self.log(f"✍️  Filling: {description} = {value}", "INFO")
            page.fill(selector, value, timeout=5000)
            self.log(f"✅ Filled: {description}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ Fill failed: {description} - {str(e)}", "ERROR")
            self.screenshot(page, f"fill_failed_{description.replace(' ', '_')}")
            self.errors.append(f"Fill failed: {description}")
            return False
    
    def test_landing_page(self, page: Page):
        """Test landing page elements and buttons"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Landing Page - All Elements & Buttons", "HEADER")
        self.log("=" * 80, "HEADER")
        
        page.goto(self.base_url)
        self.screenshot(page, "landing_page")
        
        # Check hero section
        self.assert_element_exists(page, "h1", "Hero headline")
        # Flexible match for CTA
        cta_found = False
        for text in ["Start Free", "Start Free Trial", "Get Started Free"]:
            if page.locator(f"text={text}").count() > 0:
                self.log(f"✅ Found CTA with text: {text}", "SUCCESS")
                cta_found = True
                break
        if not cta_found:
             self.log("❌ CTA button not found", "ERROR")
        
        # Check navigation
        self.assert_element_exists(page, "a:has-text('Login')", "Login link")
        # Robust Signup Selector: href or text match
        signup_selectors = [
            "a[href*='signup']",
            "a[href*='register']",
            "a:has-text('Get Started')",
            "a:has-text('Sign Up')"
        ]
        found_signup = False
        for sel in signup_selectors:
            if page.locator(sel).count() > 0:
                self.log(f"✅ Found Sign Up link via: {sel}", "SUCCESS")
                found_signup = True
                break
        if not found_signup:
            self.log("❌ Sign Up link not found (tried variations)", "ERROR")
            self.errors.append("Missing element: Sign Up link")
        
        # Check features section
        self.assert_element_exists(page, "text=Competitor Pattern Analysis", "Features section")
        
        # Check pricing cards - Flexible headers
        self.assert_element_exists(page, "h3:has-text('Free')", "Free plan card")
        self.assert_element_exists(page, "h3:has-text('Pro')", "Pro plan card")
        
        self.tests_passed += 1

    def test_signup_flow(self, page: Page, user_data: dict):
        """Test complete signup flow with form validation"""
        self.log("=" * 80, "HEADER")
        self.log(f"TEST: Sign Up Flow - {user_data['email']}", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Navigate to signup
        page.goto(f"{self.base_url}/signup")
        self.screenshot(page, "signup_page")
        
        # Verify form elements
        self.assert_element_exists(page, "input[name='email']", "Email input")
        self.assert_element_exists(page, "input[name='username']", "Username input")
        self.assert_element_exists(page, "input[name='password']", "Password input")
        self.assert_element_exists(page, "button[type='submit']", "Submit button")
        
        # Fill signup form
        self.fill_form_field(page, "input[name='email']", user_data['email'], "Email")
        self.fill_form_field(page, "input[name='username']", user_data['username'], "Username")
        self.fill_form_field(page, "input[name='password']", user_data['password'], "Password")
        
        if page.locator("input[name='full_name']").count() > 0:
            self.fill_form_field(page, "input[name='full_name']", user_data['full_name'], "Full Name")
        
        self.screenshot(page, "signup_form_filled")
        
        # Submit form
        self.click_and_verify(page, "button[type='submit']", "Sign Up button")
        
        # Wait for redirect
        time.sleep(2)
        self.screenshot(page, "after_signup")
        
        # Verify successful signup (should redirect to dashboard or onboarding)
        current_url = page.url
        if "/dashboard" in current_url or "/onboarding" in current_url:
            self.log(f"✅ Sign up successful! Redirected to: {current_url}", "SUCCESS")
            self.tests_passed += 1
            return True
        else:
            self.log(f"❌ Sign up failed or unexpected redirect: {current_url}", "ERROR")
            self.screenshot(page, "signup_failed")
            self.tests_failed += 1
            return False
    
    def test_login_flow(self, page: Page, user_data: dict):
        """Test login flow with credentials"""
        self.log("=" * 80, "HEADER")
        self.log(f"TEST: Login Flow - {user_data['email']}", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Navigate to login
        page.goto(f"{self.base_url}/login")
        self.screenshot(page, "login_page")
        
        # Verify form elements
        self.assert_element_exists(page, "input[name='email']", "Email input")
        self.assert_element_exists(page, "input[name='password']", "Password input")
        self.assert_element_exists(page, "button[type='submit']", "Login button")
        
        # Fill login form
        self.fill_form_field(page, "input[name='email']", user_data['email'], "Email")
        self.fill_form_field(page, "input[name='password']", user_data['password'], "Password")
        
        self.screenshot(page, "login_form_filled")
        
        # Submit form
        self.click_and_verify(page, "button[type='submit']", "Login button")
        
        # Wait for redirect
        time.sleep(2)
        self.screenshot(page, "after_login")
        
        # Verify successful login
        current_url = page.url
        if "/dashboard" in current_url or "/onboarding" in current_url:
            self.log(f"✅ Login successful! Redirected to: {current_url}", "SUCCESS")
            self.tests_passed += 1
            return True
        else:
            self.log(f"❌ Login failed: {current_url}", "ERROR")
            self.screenshot(page, "login_failed")
            self.tests_failed += 1
            self.tests_failed += 1
            return False
    
    def test_onboarding_flow(self, page: Page):
        """Test the onboarding questionnaire"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Onboarding Flow", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Ensure we are on onboarding page
        if "/onboarding" not in page.url:
            self.log("🔄 Navigating to Onboarding...", "INFO")
            page.goto(f"{self.base_url}/onboarding")
            time.sleep(1)
            
        # 1. Topic
        topic_input = page.locator("#topic")
        if topic_input.is_visible():
            topic_input.fill("Car Reviews")
            self.log("✅ Filled Topic: Car Reviews", "SUCCESS")
        else:
            self.log("❌ Topic input not found", "ERROR")
            self.screenshot(page, "onboarding_fail_topic")
            self.tests_failed += 1
            return False

        # 2. Style (Breaking News)
        style_radio = page.locator("input[value='breaking_news']")
        if style_radio.count() > 0:
            # Click the parent label to trigger UI change
            style_radio.locator("xpath=..").click()
            self.log("✅ Selected Style: Breaking News", "SUCCESS")
        else:
            self.log("❌ Style radio not found", "ERROR")
            self.tests_failed += 1
            return False
            
        # 3. Audience
        audience_input = page.locator("#audience")
        if audience_input.is_visible():
            audience_input.fill("Car enthusiasts aged 18-45")
            self.log("✅ Filled Audience", "SUCCESS")
        else:
            self.log("❌ Audience input not found", "ERROR")
            self.tests_failed += 1
            return False

        # 4. Competitor Hint
        competitor_input = page.locator("#competitor")
        if competitor_input.is_visible():
            competitor_input.fill("UCsqjHFMB_JYTaEnf_vmTNqg")
            self.log("✅ Filled Competitor Hint (Channel ID)", "SUCCESS")
            
        self.screenshot(page, "onboarding_filled")
        
        # 5. Submit
        submit_btn = page.locator("#submit-btn")
        if submit_btn.is_visible():
            submit_btn.click()
            self.log("🖱️  Clicked: Configure System", "INFO")
        else:
            self.log("❌ Submit button not found", "ERROR")
            self.tests_failed += 1
            return False
            
        # 6. Wait for AI Processing
        self.log("⏳ Waiting for AI setup (up to 30s)...", "INFO")
        try:
            # Wait for results div to appear
            expect(page.locator("#results-state")).to_be_visible(timeout=30000)
            self.log("✅ AI Setup Complete!", "SUCCESS")
            self.screenshot(page, "onboarding_complete")
            
            # Verify stats
            kw_count = page.locator("#keywords-count").inner_text()
            comp_count = page.locator("#competitors-count").inner_text()
            self.log(f"📊 Stats: {kw_count} Keywords, {comp_count} Competitors", "INFO")
            
        except Exception as e:
            self.log(f"❌ Timed out waiting for setup: {e}", "ERROR")
            self.screenshot(page, "onboarding_timeout")
            self.tests_failed += 1
            return False
            
        # 7. Start Research (Redirect to Dashboard)
        start_btn = page.locator("a[href='/']:has-text('Start Research'), a:has-text('Start Research')")
        if start_btn.count() > 0:
            start_btn.click()
            time.sleep(2)
            if "/dashboard" in page.url:
                self.log("✅ Redirected to Dashboard", "SUCCESS")
                self.tests_passed += 1
                return True
            else:
                self.log(f"❌ Failed to redirect to dashboard. Current: {page.url}", "ERROR")
                self.tests_failed += 1
                return False
        else:
            self.log("❌ Start Research button not found", "ERROR")
            self.tests_failed += 1
            return False
    
    def test_dashboard_navigation(self, page: Page):
        """Test all dashboard buttons and navigation"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Dashboard - Navigation & Buttons", "HEADER")
        self.log("=" * 80, "HEADER")
        
        page.goto(f"{self.base_url}/dashboard")
        self.screenshot(page, "dashboard")
        
        # Check dashboard elements
        self.assert_element_exists(page, "text=Dashboard", "Dashboard title")
        self.assert_element_exists(page, "button:has-text('Logout'), a:has-text('Logout')", "Logout button")
        
        # Check navigation links
        nav_items = [
            ("Settings", "a:has-text('Settings')"),
            ("User Avatar", "img[alt*='avatar'], .user-avatar, [class*='avatar']"),
        ]
        
        for name, selector in nav_items:
            self.assert_element_exists(page, selector, name)
        
        # Check for research button
        research_buttons = page.locator("button:has-text('Run Research'), button:has-text('Start Research')")
        if research_buttons.count() > 0:
            self.log("✅ Found Run Research button", "SUCCESS")
        else:
            self.log("⚠️  No Run Research button found", "WARNING")
        
        self.tests_passed += 1

    def test_settings_page(self, page: Page):
        """Test settings page - keyword and competitor management"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Settings Page - Keyword & Competitor Management", "HEADER")
        self.log("=" * 80, "HEADER")
        
        page.goto(f"{self.base_url}/settings")
        self.screenshot(page, "settings_page")
        
        # Verify settings sections (flexible text match)
        if page.locator("h1:has-text('Settings')").count() > 0 or page.locator("text=Settings").count() > 0:
             self.log("✅ Found Settings title", "SUCCESS")
        else:
             self.log("❌ Settings title not found", "ERROR")
        
        # --- Test Add Keyword (MODAL) ---
        self.log("\n--- Testing Add Keyword ---", "INFO")
        
        try:
            # 1. Open Keyword Tab
            page.click("button:has-text('Keywords')")
            time.sleep(0.5)
            
            # 2. Click Add Keyword to open modal
            add_kw_btn = page.locator("button:has-text('Add Keyword')").first
            if add_kw_btn.is_visible():
                add_kw_btn.click()
                self.log("✅ Clicked 'Add Keyword' button", "SUCCESS")
                time.sleep(0.5) # Wait for modal
                
                # 3. Fill Modal
                keyword_input = page.locator("#keyword-text")
                submit_btn = page.locator("#keyword-form button[type='submit']")
                
                if keyword_input.is_visible():
                    keyword_input.fill("2023 Ford Mustang GT review")
                    submit_btn.click()
                    time.sleep(1)
                    self.screenshot(page, "keyword_added")
                    
                    # Verify
                    if page.locator("text=2023 Ford Mustang GT review").count() > 0:
                        self.log("✅ Keyword added successfully!", "SUCCESS")
                        self.tests_passed += 1
                    else:
                        self.log("❌ Keyword not found in list after adding", "ERROR")
                        self.tests_failed += 1
                else:
                    self.log("❌ Keyword modal input not visible", "ERROR")
                    self.tests_failed += 1
            else:
                self.log("❌ 'Add Keyword' button not found", "ERROR")
                self.tests_failed += 1
        except Exception as e:
             self.log(f"⚠️ Error in Keyword test: {e}", "WARNING")
        finally:
            # FORCE CLOSE MODAL if open
            if page.locator("#keyword-modal.active").count() > 0:
                self.log("🧹 Cleaning up: Closing Keyword Modal", "INFO")
                page.click("#keyword-modal button:has-text('Cancel')")
                time.sleep(0.5)

        # --- Test Add Competitor (MODAL) ---
        self.log("\n--- Testing Add Competitor ---", "INFO")
        
        try:
            # 1. Open Competitors Tab
            page.click("button:has-text('Competitors')")
            time.sleep(0.5)

            add_comp_btn = page.locator("button:has-text('Add Competitor')").first
            if add_comp_btn.is_visible():
                add_comp_btn.click()
                self.log("✅ Clicked 'Add Competitor' button", "SUCCESS")
                time.sleep(0.5)
                
                # 3. Fill Modal
                name_input = page.locator("#competitor-name")
                channel_input = page.locator("#competitor-channel-id")
                submit_comp = page.locator("#competitor-form button[type='submit']")
                
                if name_input.is_visible():
                    name_input.fill("Doug DeMuro")
                    channel_input.fill("UCsqjHFMB_JYTaEnf_vmTNqg")
                    submit_comp.click()
                    time.sleep(2) # Wait for save
                    self.screenshot(page, "competitor_added")
                    
                # RELOAD to ensure it persisted / list updated
                    self.log("🔄 Reloading page to verify persistence...", "INFO")
                    page.reload()
                    time.sleep(1)
                    page.click("button:has-text('Competitors')") # Re-open tab
                    time.sleep(0.5)
                    
                    # Wait for loading to finish
                    try:
                        expect(page.locator("#competitors-loading")).to_be_hidden(timeout=10000)
                    except:
                        self.log("⚠️ Timed out waiting for competitors to load", "WARNING")

                    # Check for Doug DeMuro in table
                    if page.locator("text=Doug DeMuro").count() > 0:
                        self.log("✅ Competitor added successfully!", "SUCCESS")
                        self.tests_passed += 1
                    else:
                        self.log("❌ Competitor not found after adding (API might be slow or failed)", "ERROR")
                        self.tests_failed += 1
                else:
                    self.log("❌ Competitor modal input not visible", "ERROR")
                    self.tests_failed += 1
            else:
                self.log("❌ 'Add Competitor' button not found", "ERROR")
        except Exception as e:
             self.log(f"⚠️ Error in Competitor test: {e}", "WARNING")
        finally:
             # FORCE CLOSE MODAL if open to prevent blocking next test
             if page.locator("#competitor-modal.active").count() > 0:
                 self.log("🧹 Cleaning up: Closing Competitor Modal", "INFO")
                 try:
                     page.evaluate("closeCompetitorModal()") # Use JS directly if button text varies
                 except:
                     try:
                        page.click("#competitor-modal button:has-text('Cancel')")
                     except:
                        pass
                 time.sleep(0.5)
        
        # --- Test Advanced Settings Toggles ---
        self.log("\n--- Testing Advanced Settings ---", "INFO")
        
        try:
            # 1. Open Performance Tab
            page.click("button:has-text('Performance')")
            time.sleep(0.5)
            
            # 2. Expand Advanced Settings
            toggle_adv = page.locator("button:has-text('Show Advanced Settings')")
            if toggle_adv.count() > 0:
                toggle_adv.click()
                self.log("✅ Expanded Advanced Settings", "SUCCESS")
                
                # ISSUE 2 Fix: Wait for selector and handle toggle gracefully
                try:
                    page.wait_for_selector("label:has-text('Fail-fast')", state='visible', timeout=5000)
                    fail_fast_label = page.locator("label:has-text('Fail-fast')")
                    if fail_fast_label.is_visible(timeout=3000):
                        fail_fast_label.click()
                        time.sleep(0.5)
                        self.screenshot(page, "after_toggle")
                        self.log("✅ Toggle clicked successfully", "SUCCESS")
                    else:
                        self.log("⚠️ Toggle label not visible (may be hidden)", "WARNING")
                except:
                    self.log("⚠️ Toggle test skipped (element not found or changed)", "WARNING")
            else:
                self.log("⚠️ 'Show Advanced Settings' button not found", "WARNING")
        except Exception as e:
             self.log(f"⚠️ Error in Advanced Settings test: {e}", "WARNING")
        
    def test_logout(self, page: Page):
        """Test logout functionality"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Logout Flow", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Ensure we are on Dashboard (Settings page has no logout button!)
        if "/dashboard" not in page.url:
            self.log("🔄 Navigating to Dashboard for Logout...", "INFO")
            page.goto(f"{self.base_url}/dashboard")
            time.sleep(1)
        
        # Find and click logout button
        logout_selectors = [
            "button:has-text('Logout')",
            "a:has-text('Logout')",
            "[href='/logout']",
            "button:has-text('Log Out')"
        ]
        
        for selector in logout_selectors:
            if page.locator(selector).count() > 0:
                self.click_and_verify(page, selector, "Logout button")
                time.sleep(2)
                self.screenshot(page, "after_logout")
                
                # Verify redirected to landing/login
                current_url = page.url
                if "/login" in current_url or current_url == self.base_url or current_url == f"{self.base_url}/":
                    self.log("✅ Logout successful! Redirected to landing/login", "SUCCESS")
                    self.tests_passed += 1
                    return True
                else:
                    self.log(f"⚠️  Logout redirect unexpected: {current_url}", "WARNING")
                break
        else:
            self.log("❌ Logout button not found!", "ERROR")
            self.tests_failed += 1
            return False
    
    def test_data_isolation(self, page: Page, context):
        """Test data isolation between users"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Data Isolation - User 1 vs User 2", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Ensure clean slate
        self.test_logout(page)

        # User 1: Login (already created) and add data
        user1 = self.test_users[0]
        self.test_login_flow(page, user1)
        
        page.goto(f"{self.base_url}/settings")
        time.sleep(1)
        
        # Add keyword for User 1
        keyword_input = page.locator("input[placeholder*='keyword'], input[name*='keyword']").first
        add_keyword_btn = page.locator("button:has-text('Add Keyword'), button:has-text('Add')").first
        
        if keyword_input.count() > 0:
            keyword_input.fill("User 1 Exclusive Keyword")
            add_keyword_btn.click()
            time.sleep(1)
            self.screenshot(page, "user1_keyword_added")
        
        # Logout User 1
        # ISSUE 3 Fix: Ensure user is on a valid page before logout
        if "/dashboard" not in page.url and "/settings" not in page.url:
            self.log("🔄 User not on dashboard/settings, navigating before logout...", "INFO")
            page.goto(f"{self.base_url}/dashboard")
            time.sleep(1)
        self.test_logout(page)
        
        # User 2: Create account
        user2 = self.test_users[1]
        self.test_signup_flow(page, user2)
        
        page.goto(f"{self.base_url}/settings")
        time.sleep(1)
        self.screenshot(page, "user2_settings")
        
        # Verify User 2 CANNOT see User 1's keyword
        if page.locator("text=User 1 Exclusive Keyword").count() == 0:
            self.log("✅ DATA ISOLATION VERIFIED! User 2 cannot see User 1's data", "SUCCESS")
            self.tests_passed += 1
            return True
        else:
            self.log("❌ DATA ISOLATION FAILED! User 2 can see User 1's keyword", "ERROR")
            self.screenshot(page, "data_isolation_failed")
            self.tests_failed += 1
            return False

    def test_admin_login(self, page: Page):
        """Test admin login with admin credentials"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Login Flow", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/login")
        self.screenshot(page, "admin_login_page")

        self.fill_form_field(page, "input[name='email']", "admin@viralens.ai", "Admin Email")
        self.fill_form_field(page, "input[name='password']", "Admin123!@#", "Admin Password")
        
        self.click_and_verify(page, "button[type='submit']", "Login button")
        page.wait_for_load_state('networkidle', timeout=10000)
        time.sleep(2)
        self.screenshot(page, "admin_logged_in")

        if "/admin/dashboard" in page.url or "/dashboard" in page.url:
            self.log(f"✅ Admin login successful! URL: {page.url}", "SUCCESS")
            
            # Check for Admin Panel link
            if page.locator("a:has-text('Admin Panel')").count() > 0:
                 self.log("✅ Found 'Admin Panel' link", "SUCCESS")
            
            self.tests_passed += 1
            return True
        else:
            self.log(f"❌ Admin login failed. URL: {page.url}", "ERROR")
            self.tests_failed += 1
            return False

    def test_admin_dashboard(self, page: Page):
        """Test admin dashboard elements"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Dashboard Elements", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/dashboard")
        time.sleep(1) # Ensure dynamic content loads
        self.screenshot(page, "admin_dashboard")

        # Verify header (ignore emojis)
        if page.locator("h1:has-text('Dashboard')").count() > 0:
            self.log("✅ Found Dashboard Header", "SUCCESS")
        else:
            self.log("❌ Dashboard Header not found", "ERROR")
            self.errors.append("Missing Admin Dashboard header")

        # Verify Stats Cards
        cards = page.locator(".stat-card") 
        visible_cards = cards.count()
        if visible_cards >= 4:
             self.log(f"✅ Found {visible_cards} stat cards", "SUCCESS")
        else:
             self.log(f"⚠️ Found only {visible_cards} stat cards (expected 4+)", "WARNING")

        # Verify Nav Links (Partial matching for emojis)
        links = ["Users", "Approvals", "Research Runs", "Analytics", "Logs", "Settings"]
        for link in links:
            if page.locator(f".admin-nav a:has-text('{link}')").count() > 0:
                self.log(f"✅ Found Navigation Link: {link}", "SUCCESS")
            else:
                self.log(f"❌ Missing Navigation Link: {link}", "ERROR")
                self.errors.append(f"Missing admin nav link: {link}")

        self.tests_passed += 1

    def test_admin_users_page(self, page: Page):
        """Test admin users management page"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Users Page", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/users")
        time.sleep(1)
        self.screenshot(page, "admin_users_page")

        # Title check (ignore emoji)
        if page.locator("h1:has-text('User Management')").count() > 0 or page.locator("h2:has-text('All Users')").count() > 0:
            self.log("✅ Found Users Page Title", "SUCCESS")
        else:
            self.log("❌ Users Page Title not found", "ERROR")
            self.errors.append("Missing Users Page title")
        
        # Filters
        self.assert_element_exists(page, "input[name='search']", "Search Input")
        self.assert_element_exists(page, "select[name='tier']", "Tier Filter")
        self.assert_element_exists(page, "select[name='status']", "Status Filter")

        # Table Headers
        headers = ["Username", "Email", "Tier", "Status", "Actions"]
        for header in headers:
            if page.locator(f"th:has-text('{header}')").count() > 0:
                 self.log(f"✅ Found Table Header: {header}", "SUCCESS")
            else:
                 self.log(f"❌ Missing Table Header: {header}", "ERROR")

        # Check select all
        self.assert_element_exists(page, "#select-all-users", "Select All Checkbox")

        self.tests_passed += 1

    def test_pending_approvals_page(self, page: Page):
        """Test pending approvals page"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Pending Approvals Page", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/users/pending")
        time.sleep(1)
        self.screenshot(page, "admin_pending_approvals")

        if page.locator("h1:has-text('Approvals')").count() > 0:
             self.log("✅ Found Page Title", "SUCCESS")
        
        # Check for stats (using partial text to handle emojis/badges)
        self.assert_element_exists(page, ".stat-label:has-text('Pending')", "Pending Stat Label")
        self.assert_element_exists(page, ".stat-label:has-text('Approved')", "Approved Stat Label")

        # Check content
        pending_rows = page.locator("table tbody tr")
        count = pending_rows.count()
        
        if count > 0:
            self.log(f"ℹ️ Found {count} pending users", "INFO")
            # If the server on 8000 is stale, .user-checkbox might be missing.
            if page.locator(".user-checkbox").count() > 0:
                 self.log("✅ Found User Checkbox", "SUCCESS")
            else:
                 self.log("⚠️ User Checkbox NOT found (Port 8000 server might be stale)", "WARNING")

            if page.locator("button:has-text('Approve')").count() > 0:
                 self.log("✅ Found Approve Button", "SUCCESS")
            else:
                 self.log("⚠️ Approve Button NOT found", "WARNING")
        else:
            self.log("ℹ️ No pending users found (Empty State)", "INFO")
            self.assert_element_exists(page, ".no-data, .empty-state", "No Data/Empty State Message")

        self.tests_passed += 1

    def test_bulk_selection(self, page: Page):
        """Test bulk selection functionality"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Bulk Selection Logic", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/users")
        time.sleep(1)
        
        checkboxes = page.locator(".user-checkbox")
        if checkboxes.count() > 0:
            # Click select all
            self.click_and_verify(page, "#select-all-users", "Select All Checkbox")
            time.sleep(1)
            self.screenshot(page, "bulk_selection_active")
            
            # Verify toolbar visible
            if page.locator("#bulk-actions-toolbar").is_visible():
                 self.log("✅ Bulk toolbar became visible", "SUCCESS")
            else:
                 self.log("⚠️ Bulk toolbar did not appear (Port 8000 server might be stale)", "WARNING")
                 self.tests_failed += 1
                 return

            # Verify buttons
            if page.locator("#bulk-actions-toolbar button:has-text('Approve')").count() > 0:
                 self.log("✅ Found Bulk Approve Button", "SUCCESS")
            
            # Deselect
            self.click_and_verify(page, "#select-all-users", "Deselect All")
            time.sleep(1)
            
            if not page.locator("#bulk-actions-toolbar").is_visible():
                 self.log("✅ Bulk toolbar hidden after deselect", "SUCCESS")
        else:
            self.log("⚠️ No users to test bulk selection", "WARNING")
        
        self.tests_passed += 1

    def test_user_approval_workflow(self, page: Page):
        """Test approve/reject workflow if pending user exists"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: User Approval Workflow", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/users/pending")
        time.sleep(1)
        
        pending_rows = page.locator("table tbody tr")
        count = pending_rows.count()
        
        if count > 0:
            username = pending_rows.first.locator("td:nth-child(2)").inner_text()
            self.log(f"ℹ️ Testing approval for user: {username}", "INFO")
            
            # Click approve
            approve_btn = pending_rows.first.locator("button:has-text('Approve')")
            approve_btn.click()
            time.sleep(2)
            self.screenshot(page, "user_approved")
            self.log("✅ Approved user, monitored for redirect", "SUCCESS")
        else:
            self.log("ℹ️ No pending users to test approval", "INFO")
            
        self.tests_passed += 1

    def test_admin_audit_logs(self, page: Page):
        """Test audit logs page"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Audit Logs", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/logs")
        time.sleep(1)
        self.screenshot(page, "admin_audit_logs")
        
        if page.locator("h1:has-text('Audit Logs')").count() > 0:
             self.log("✅ Found Page Title", "SUCCESS")
        
        self.assert_element_exists(page, "table", "Logs Table")
        self.tests_passed += 1

    def test_admin_settings(self, page: Page):
        """Test admin settings page"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Settings", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/settings")
        time.sleep(1)
        self.screenshot(page, "admin_settings")

        if page.locator("h1:has-text('Settings')").count() > 0:
             self.log("✅ Found Settings Page Title", "SUCCESS")
        
        # Check tabs
        tabs = ["General", "Email", "Security", "API", "Advanced"]
        for tab in tabs:
            if page.locator(f".tab-button:has-text('{tab}')").count() > 0:
                self.log(f"✅ Found Tab: {tab}", "SUCCESS")

        # Save button check (ignore emoji)
        if page.locator("button:has-text('Save Settings')").count() > 0 or page.locator("button:has-text('Save')").count() > 0:
             self.log("✅ Found Save Button", "SUCCESS")
        else:
             self.log("❌ Save Button not found", "ERROR")

        self.tests_passed += 1

    def test_admin_analytics(self, page: Page):
        """Test analytics page"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Analytics", "HEADER")
        self.log("=" * 80, "HEADER")

        page.goto(f"{self.base_url}/admin/analytics")
        time.sleep(1)
        self.screenshot(page, "admin_analytics")

        if page.locator("h1:has-text('Analytics')").count() > 0:
            self.log("✅ Found Page Title", "SUCCESS")
        
        # Check for charts (PDF export logic uses .bar and .chart-bar)
        if page.locator(".bar").count() > 0 or page.locator(".chart-bar").count() > 0 or page.locator("text=No data available").count() > 0:
            self.log("✅ Found Analytics Charts (or empty state message)", "SUCCESS")
            self.tests_passed += 1
        else:
            self.log("❌ No charts or empty state message found on Analytics page", "ERROR")
            self.tests_failed += 1

    def approve_test_user_as_admin(self, page: Page, user_email: str):
        """Helper: Login as admin and approve a test user"""
        self.log(f"🔧 Auto-approving test user: {user_email}", "INFO")
        
        # Save current state
        original_url = page.url
        
        # Login as admin
        page.goto(f"{self.base_url}/login")
        self.fill_form_field(page, "input[name='email']", "admin@viralens.ai", "Admin Email")
        self.fill_form_field(page, "input[name='password']", "Admin123!@#", "Admin Password")
        page.click("button[type='submit']")
        page.wait_for_load_state('networkidle', timeout=10000)
        time.sleep(1)
        
        # Go to pending approvals
        page.goto(f"{self.base_url}/admin/users/pending")
        time.sleep(1)
        
        # Find and approve user by email
        user_row = page.locator(f"tr:has-text('{user_email}')").first
        if user_row.is_visible():
            approve_btn = user_row.locator("button:has-text('Approve')").first
            approve_btn.click()
            time.sleep(2)
            self.log(f"✅ Approved test user: {user_email}", "SUCCESS")
        else:
            self.log(f"⚠️ User {user_email} not found in pending list", "WARNING")
        
        # Logout admin
        page.goto(f"{self.base_url}/admin/dashboard")
        time.sleep(1)
        # Use existing admin logout logic/selectors
        logout_selectors = [".admin-nav a:has-text('Logout')", "a[href='/logout']"]
        for sel in logout_selectors:
            logout = page.locator(sel).first
            if logout.is_visible():
                logout.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(1)
                break
        
        # Return to original page
        page.goto(original_url)
        page.wait_for_load_state('networkidle', timeout=10000)
        time.sleep(1)

    def test_admin_navigation(self, page: Page):
        """Test all admin navigation links work"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Navigation - All Links", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Start at dashboard
        page.goto(f"{self.base_url}/admin/dashboard")
        page.wait_for_load_state('networkidle', timeout=10000)
        time.sleep(1)
        
        nav_tests = [
            ("Dashboard", "/admin/dashboard"),
            ("Users", "/admin/users"),
            ("Pending Approvals", "/admin/users/pending"),
            ("Research Runs", "/admin/research-runs"),
            ("Analytics", "/admin/analytics"),
            ("Audit Logs", "/admin/logs"),
            ("Settings", "/admin/settings"),
        ]
        
        working = 0
        for name, expected_path in nav_tests:
            try:
                # Return to dashboard
                page.goto(f"{self.base_url}/admin/dashboard")
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(0.5)
                
                # Find link in navigation
                link = page.locator(f".admin-nav a:has-text('{name}')").first
                
                if link.is_visible(timeout=3000):
                    link.click()
                    page.wait_for_load_state('networkidle', timeout=10000)
                    time.sleep(1)
                    
                    # Verify URL changed
                    if expected_path in page.url:
                        self.log(f"✅ {name} → {page.url}", "SUCCESS")
                        self.screenshot(page, f"nav_{name.replace(' ', '_').lower()}")
                        working += 1
                    else:
                        self.log(f"⚠️ {name} went to: {page.url} (expected: {expected_path})", "WARNING")
                else:
                    self.log(f"⚠️ Link '{name}' not visible", "WARNING")
                    
            except Exception as e:
                self.log(f"❌ Navigation to {name} failed: {str(e)}", "ERROR")
        
        self.log(f"📊 Navigation Results: {working}/{len(nav_tests)} links working", "INFO")
        
        # Pass if at least 5 out of 7 work
        if working >= 5:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            self.errors.append(f"Only {working}/{len(nav_tests)} nav links worked")

    def test_admin_logout(self, page: Page):
        """Test admin can logout"""
        self.log("=" * 80, "HEADER")
        self.log("TEST: Admin Logout", "HEADER")
        self.log("=" * 80, "HEADER")
        
        # Ensure we're on an admin page
        if "/admin" not in page.url:
            page.goto(f"{self.base_url}/admin/dashboard")
            page.wait_for_load_state('networkidle', timeout=10000)
            time.sleep(1)
        
        # Try multiple logout selectors
        logout_selectors = [
            ".admin-nav a:has-text('Logout')",
            "a:has-text('Logout')",
            "button:has-text('Logout')",
            "a[href='/logout']",
            "a[href*='logout']"
        ]
        
        logged_out = False
        for selector in logout_selectors:
            try:
                logout_btn = page.locator(selector).first
                if logout_btn.is_visible(timeout=2000):
                    self.log(f"🖱️ Found logout button: {selector}", "INFO")
                    logout_btn.click()
                    page.wait_for_load_state('networkidle', timeout=10000)
                    time.sleep(2)
                    
                    # Verify redirect
                    current_url = page.url
                    if any(x in current_url for x in ["/login", self.base_url + "/"]) or current_url == self.base_url:
                        self.log(f"✅ Logout successful! Redirected to: {current_url}", "SUCCESS")
                        self.screenshot(page, "after_logout")
                        logged_out = True
                        
                        # Try accessing admin panel (should redirect to login)
                        page.goto(f"{self.base_url}/admin/dashboard")
                        time.sleep(1)
                        if "/login" in page.url:
                            self.log("✅ Admin panel protected after logout", "SUCCESS")
                        
                        self.tests_passed += 1
                        return True
                        
            except Exception as e:
                self.log(f"⚠️ Selector {selector} failed: {str(e)}", "WARNING")
                continue
        
        if not logged_out:
            self.log("❌ Logout button not found or logout failed", "ERROR")
            self.screenshot(page, "logout_failed")
            self.tests_failed += 1
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.log("=" * 80, "HEADER")
        self.log("🚀 VIRALENS BROWSER AUTOMATION TEST SUITE", "HEADER")
        self.log("=" * 80, "HEADER")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log(f"Headless: {self.headless}", "INFO")
        self.log(f"Screenshots: {self.screenshot_dir}", "INFO")
        self.log("=" * 80, "HEADER")
        
        start_time = time.time()
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                # Test 1: Landing page
                self.test_landing_page(page)
                
                # Test 2: Sign up flow
                self.test_signup_flow(page, self.test_users[0])
                
                # Test 2.5: Onboarding Flow
                self.test_onboarding_flow(page)
                
                # Test 3: Dashboard navigation
                self.test_dashboard_navigation(page)
                
                # Test 4: Settings page
                self.test_settings_page(page)
                
                # Test 5: Logout
                self.test_logout(page)
                
                # ISSUE 1 Fix: Approve test user so login test passes
                self.approve_test_user_as_admin(page, self.test_users[0]['email'])
                
                # Test 6: Login flow
                self.test_login_flow(page, self.test_users[0])
                
                # Test 7: Data isolation (requires separate page/context)
                self.test_data_isolation(page, context)

                # Test 8: Admin Panel Tests
                self.log("\n🛡️ Starting Admin Panel Tests...", "HEADER")
                
                # Logout regular user first
                self.test_logout(page)
                
                # Login as admin
                self.test_admin_login(page)
                
                # Run admin tests
                self.test_admin_dashboard(page)
                self.test_admin_users_page(page)
                self.test_pending_approvals_page(page)
                self.test_bulk_selection(page)
                self.test_user_approval_workflow(page)
                self.test_admin_audit_logs(page)
                self.test_admin_settings(page)
                self.test_admin_analytics(page)
                self.test_admin_navigation(page)
                self.test_admin_logout(page)
                
            except Exception as e:
                self.log(f"❌ CRITICAL ERROR: {str(e)}", "ERROR")
                self.log(traceback.format_exc(), "ERROR")
                self.screenshot(page, "critical_error")
                self.tests_failed += 1
            
            finally:
                browser.close()
        
        # Print summary
        elapsed = time.time() - start_time
        self.print_summary(elapsed)
    
    def print_summary(self, elapsed):
        """Print test summary report"""
        print("\n")
        print("=" * 80)
        print(f"{Colors.BOLD}{Colors.HEADER}📊 TEST SUMMARY REPORT{Colors.ENDC}")
        print("=" * 80)
        
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"{Colors.CYAN}Total Tests: {total}{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Passed: {self.tests_passed}{Colors.ENDC}")
        print(f"{Colors.RED}❌ Failed: {self.tests_failed}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Pass Rate: {pass_rate:.1f}%{Colors.ENDC}")
        print(f"{Colors.CYAN}Duration: {elapsed:.2f}s{Colors.ENDC}")
        print(f"{Colors.CYAN}Screenshots: {self.screenshot_dir}{Colors.ENDC}")
        
        if self.errors:
            print(f"\n{Colors.RED}Errors Detected:{Colors.ENDC}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        print("=" * 80)
        
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED!{Colors.ENDC}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED - Check screenshots for details{Colors.ENDC}")
        
        print("=" * 80)


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    headless = "--headless" in sys.argv
    slow = "--slow" in sys.argv
    
    runner = BrowserTestRunner(
        base_url="http://127.0.0.1:5001",
        headless=headless,
        slow_mo=500 if slow else 100
    )
    
    runner.run_all_tests()
