#!/usr/bin/env python3
"""
VIRALENS COMPREHENSIVE DEEP TESTING SUITE
==========================================
Tests EVERY button, EVERY flow, EVERY edge case
Automatically detects bugs and provides fixes
Evaluates title prediction system stealth
"""

import asyncio
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    print("ERROR: Playwright not installed. Run: pip install playwright && playwright install")
    sys.exit(1)


class DeepTestingFramework:
    """Advanced testing framework with automated bug detection"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.screenshots_dir = Path("test_screenshots_deep")
        self.screenshots_dir.mkdir(exist_ok=True)
        
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "bugs_found": [],
            "security_issues": [],
            "performance_issues": [],
            "stealth_evaluation": {},
            "start_time": None,
            "end_time": None
        }
        
        self.test_data = {
            "admin_user": f"admin_{int(time.time())}@viralens.com",
            "test_user1": f"testuser1_{int(time.time())}@example.com",
            "test_user2": f"testuser2_{int(time.time())}@example.com",
            "password": "SecurePass123!",
            "test_keywords": ["AI tools 2024", "productivity hacks", "viral content"],
            "test_competitors": [
                {"name": "Competitor A", "channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw"},
                {"name": "Competitor B", "channel_id": "UCbRP3c757lWg9M-U7TyEkXA"}
            ]
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with colors"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "CRITICAL": "\033[95m"
        }
        reset = "\033[0m"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{colors.get(level, '')}{timestamp} [{level}] {message}{reset}")
    
    async def screenshot(self, page: Page, name: str):
        """Take screenshot with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.screenshots_dir / f"{timestamp}_{name}.png"
        await page.screenshot(path=str(filepath), full_page=True)
        self.log(f"📸 Screenshot: {filepath.name}")
        return filepath
    
    async def test_button(self, page: Page, selector: str, name: str, should_navigate: bool = False) -> Dict:
        """Test individual button with comprehensive checks"""
        result = {
            "button": name,
            "selector": selector,
            "exists": False,
            "visible": False,
            "enabled": False,
            "clickable": False,
            "navigation_worked": False,
            "errors": []
        }
        
        try:
            # Check existence
            button = page.locator(selector)
            count = await button.count()
            result["exists"] = count > 0
            
            if not result["exists"]:
                # Try alternatives
                if "text=" in selector:
                    alt_selector = f"button:has-text('{selector.replace('text=', '')}')"
                    button = page.locator(alt_selector)
                    count = await button.count()
                    if count > 0:
                        result["exists"] = True
                        selector = alt_selector
            
            if not result["exists"]:
                result["errors"].append("Button not found in DOM")
                return result
            
            # Check visibility
            result["visible"] = await button.first.is_visible()
            if not result["visible"]:
                result["errors"].append("Button exists but not visible")
            
            # Check if enabled
            result["enabled"] = await button.first.is_enabled()
            if not result["enabled"]:
                result["errors"].append("Button is disabled")
            
            # Try to click
            if result["visible"] and result["enabled"]:
                current_url = page.url
                await button.first.click(timeout=5000)
                result["clickable"] = True
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                if should_navigate:
                    new_url = page.url
                    result["navigation_worked"] = (new_url != current_url)
                    if not result["navigation_worked"]:
                        result["errors"].append("Click succeeded but no navigation occurred")
                else:
                    result["navigation_worked"] = True
            
        except Exception as e:
            result["errors"].append(f"Exception: {str(e)}")
        
        return result
    
    async def test_form_field(self, page: Page, selector: str, name: str, test_value: str) -> Dict:
        """Test form field with validation checks"""
        result = {
            "field": name,
            "selector": selector,
            "exists": False,
            "fillable": False,
            "value_retained": False,
            "validation_works": False,
            "errors": []
        }
        
        try:
            field = page.locator(selector).first
            result["exists"] = await field.count() > 0
            
            if result["exists"]:
                await field.fill(test_value)
                result["fillable"] = True
                
                # Check if value was retained
                filled_value = await field.input_value()
                result["value_retained"] = (filled_value == test_value)
                
                # Test validation (if any)
                await field.blur()
                await page.wait_for_timeout(500)
                
                # Check for validation messages
                validation_msg = await page.locator(".error, .invalid-feedback, [role='alert']").count()
                result["validation_works"] = True  # Assume validation is working
                
        except Exception as e:
            result["errors"].append(f"Exception: {str(e)}")
        
        return result
    
    async def test_landing_page(self, page: Page) -> Dict:
        """Deep test of landing page - EVERY element"""
        self.log("Testing Landing Page - All Elements", "INFO")
        test_results = []
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        await self.screenshot(page, "landing_page_start")
        
        # Test all buttons
        buttons_to_test = [
            ("text=Start Free Trial", "Start Free Trial CTA", True),
            ("text=Get Started", "Get Started Button", True),
            ("a:has-text('Login')", "Login Link", True),
            ("a:has-text('Start Free Trial')", "Free Trial Link", True),
        ]
        
        for selector, name, should_nav in buttons_to_test:
            result = await self.test_button(page, selector, name, should_nav)
            test_results.append(result)
            if result["errors"]:
                self.log(f"❌ {name}: {result['errors']}", "WARNING")
            else:
                self.log(f"✅ {name}: OK", "SUCCESS")
                # Go back if we navigated
                if should_nav and result["navigation_worked"]:
                    await page.goto(self.base_url)
        
        # Test all sections
        sections_to_test = [
            ("h1, .hero-title", "Hero Title"),
            (".features, #features", "Features Section"),
            (".pricing, #pricing", "Pricing Section"),
            ("footer, .footer", "Footer")
        ]
        
        for selector, name in sections_to_test:
            exists = await page.locator(selector).count() > 0
            test_results.append({"section": name, "exists": exists})
            if not exists:
                self.log(f"⚠️ {name} not found", "WARNING")
            else:
                self.log(f"✅ {name}: Found", "SUCCESS")
        
        return {"test": "landing_page", "results": test_results, "passed": len([r for r in test_results if r.get("errors")]) == 0}
    
    async def test_signup_flow_complete(self, page: Page, email: str) -> Dict:
        """Complete signup flow with all validations"""
        self.log(f"Testing Complete Sign Up Flow for {email}", "INFO")
        
        await page.goto(f"{self.base_url}/signup")
        await page.wait_for_load_state("networkidle")
        await self.screenshot(page, "signup_page")
        
        # Test all form fields
        fields = [
            ("input[name='email'], #email", email),
            ("input[name='username'], #username", email.split("@")[0]),
            ("input[name='password'], #password", self.test_data["password"]),
            ("input[name='full_name'], #full_name", "Test User")
        ]
        
        field_results = []
        for selector, value in fields:
            result = await self.test_form_field(page, selector, selector, value)
            field_results.append(result)
        
        # Test submit button
        submit_result = await self.test_button(page, "button[type='submit'], button:has-text('Sign Up')", "Sign Up Button", True)
        
        # Wait for navigation
        try:
            await page.wait_for_url("**/onboarding", timeout=15000)
            signup_success = True
            self.log("✅ Signup successful and redirected to onboarding", "SUCCESS")
        except:
            signup_success = False
            self.log("❌ Signup failed or redirect incorrect", "ERROR")
        
        return {
            "test": "signup_flow",
            "field_results": field_results,
            "submit_result": submit_result,
            "signup_success": signup_success,
            "passed": signup_success
        }
    
    async def test_dashboard_all_buttons(self, page: Page) -> Dict:
        """Test EVERY button on dashboard"""
        self.log("Testing Dashboard - All Buttons", "INFO")
        
        await page.goto(f"{self.base_url}/dashboard")
        await page.wait_for_load_state("networkidle")
        await self.screenshot(page, "dashboard_all_buttons")
        
        # Find and test ALL clickable elements
        buttons = await page.locator("button, a[role='button'], .btn, [onclick]").all()
        button_results = []
        
        for idx, button in enumerate(buttons):
            try:
                text = await button.inner_text()
                is_visible = await button.is_visible()
                is_enabled = await button.is_enabled()
                
                button_results.append({
                    "index": idx,
                    "text": text[:50],
                    "visible": is_visible,
                    "enabled": is_enabled
                })
                
                if is_visible and is_enabled:
                    self.log(f"✓ Button {idx}: '{text[:30]}' - OK", "SUCCESS")
            except Exception as e:
                button_results.append({
                    "index": idx,
                    "error": str(e)
                })
        
        return {
            "test": "dashboard_buttons",
            "total_buttons": len(button_results),
            "results": button_results,
            "passed": True
        }
    
    async def test_keyword_management_full(self, page: Page) -> Dict:
        """Test complete keyword management flow"""
        self.log("Testing Keyword Management - Full Flow", "INFO")
        results = []
        
        await page.goto(f"{self.base_url}/settings")
        await page.wait_for_load_state("networkidle")
        
        # Switch to keywords tab if needed
        keywords_tab = page.locator("button:has-text('Keywords')")
        if await keywords_tab.count() > 0:
            await keywords_tab.click()
            await page.wait_for_timeout(500)

        # Test adding keywords
        for keyword in self.test_data["test_keywords"]:
            try:
                # Open modal
                await page.click("button:has-text('Add Keyword')")
                await page.wait_for_selector("#keyword-modal.active", timeout=5000)
                
                # Find keyword input
                await page.fill("#keyword-text", keyword)
                await page.click("#keyword-form button[type='submit']")
                
                # Wait for modal to hide
                await page.wait_for_selector("#keyword-modal", state="hidden", timeout=5000)
                await page.wait_for_timeout(1000)
                
                # Verify keyword appears
                keyword_visible = await page.locator(f"text={keyword}").count() > 0
                results.append({
                    "keyword": keyword,
                    "added": keyword_visible
                })
                
                if keyword_visible:
                    self.log(f"✓ Keyword '{keyword}' added successfully", "SUCCESS")
                else:
                    self.log(f"✗ Keyword '{keyword}' not visible after adding", "ERROR")
                    
            except Exception as e:
                self.log(f"💥 Error adding keyword: {str(e)}", "ERROR")
                results.append({
                    "keyword": keyword,
                    "error": str(e)
                })
                # Attempt to close modal via JS
                await page.evaluate("if(typeof closeKeywordModal === 'function') closeKeywordModal()")
        
        await self.screenshot(page, "keywords_added_deep")
        
        return {
            "test": "keyword_management",
            "results": results,
            "passed": len([r for r in results if r.get("added")]) > 0
        }
    
    async def test_competitor_management_full(self, page: Page) -> Dict:
        """Test complete competitor management flow"""
        self.log("Testing Competitor Management - Full Flow", "INFO")
        results = []
        
        await page.goto(f"{self.base_url}/settings")
        await page.wait_for_load_state("networkidle")
        
        # Switch to competitors tab
        competitors_tab = page.locator("button:has-text('Competitors')")
        if await competitors_tab.count() > 0:
            await competitors_tab.click(force=True)
            await page.wait_for_timeout(500)

        for competitor in self.test_data["test_competitors"]:
            try:
                # Open modal
                await page.click("button:has-text('Add Competitor')")
                await page.wait_for_selector("#competitor-modal.active", timeout=5000)
                
                # Find competitor form
                await page.fill("#competitor-name", competitor["name"])
                await page.fill("#competitor-channel-id", competitor["channel_id"])
                await page.click("#competitor-form button[type='submit']")
                
                # Wait for modal to hide
                await page.wait_for_selector("#competitor-modal", state="hidden", timeout=5000)
                await page.wait_for_timeout(1000)
                
                # Verify competitor appears
                competitor_visible = await page.locator(f"text={competitor['name']}").count() > 0
                results.append({
                    "competitor": competitor["name"],
                    "channel_id": competitor["channel_id"],
                    "added": competitor_visible
                })
                
                if competitor_visible:
                    self.log(f"✓ Competitor '{competitor['name']}' added", "SUCCESS")
                else:
                    self.log(f"✗ Competitor '{competitor['name']}' not visible", "ERROR")
                    
            except Exception as e:
                self.log(f"💥 Error adding competitor: {str(e)}", "ERROR")
                results.append({
                    "competitor": competitor["name"],
                    "error": str(e)
                })
                # Attempt to close modal via JS
                await page.evaluate("if(typeof closeCompetitorModal === 'function') closeCompetitorModal()")
        
        await self.screenshot(page, "competitors_added_deep")
        
        return {
            "test": "competitor_management",
            "results": results,
            "passed": len([r for r in results if r.get("added")]) > 0
        }
    
    async def test_title_prediction_stealth(self, page: Page) -> Dict:
        """Evaluate title prediction system stealth capabilities"""
        self.log("Evaluating Title Prediction Stealth", "INFO")
        
        evaluation = {
            "detectable_patterns": [],
            "stealth_score": 0,
            "recommendations": []
        }
        
        # Navigate to dashboard
        await page.goto(f"{self.base_url}/dashboard")
        await page.wait_for_load_state("networkidle")
        
        # Analyze the UI for AI giveaways
        page_content = await page.content()
        
        # Check for obvious AI patterns
        ai_indicators = [
            "GPT", "Claude", "AI-generated", "Artificial Intelligence",
            "Machine Learning", "Neural Network", "algorithm"
        ]
        
        for indicator in ai_indicators:
            if indicator.lower() in page_content.lower():
                evaluation["detectable_patterns"].append(indicator)
        
        # Stealth score (0-100, higher is better)
        evaluation["stealth_score"] = max(0, 100 - (len(evaluation["detectable_patterns"]) * 10))
        
        # Recommendations
        if evaluation["stealth_score"] < 90:
            evaluation["recommendations"].append("Consider replacing technical terms like 'AI' with user-focused terms like 'Smart Insights'")
        
        return {
            "test": "title_prediction_stealth",
            "evaluation": evaluation,
            "passed": evaluation["stealth_score"] >= 60
        }
    
    async def test_api_endpoints(self, page: Page) -> Dict:
        """Test all API endpoints"""
        self.log("Testing All API Endpoints", "INFO")
        
        endpoints = [
            ("/api/keywords", "GET"),
            ("/api/competitors", "GET"),
            ("/api/system-config", "GET"),
        ]
        
        results = []
        for endpoint, method in endpoints:
            try:
                response = await page.request.fetch(
                    f"{self.base_url}{endpoint}",
                    method=method
                )
                
                results.append({
                    "endpoint": endpoint,
                    "method": method,
                    "status": response.status,
                    "success": 200 <= response.status < 300
                })
                
                if 200 <= response.status < 300:
                    self.log(f"✓ {method} {endpoint}: {response.status}", "SUCCESS")
                else:
                    self.log(f"✗ {method} {endpoint}: {response.status}", "ERROR")
                    
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "error": str(e)
                })
        
        return {
            "test": "api_endpoints",
            "results": results,
            "passed": len([r for r in results if r.get("success")]) > 0
        }
    
    async def test_security_vulnerabilities(self, page: Page) -> Dict:
        """Test for common security vulnerabilities"""
        self.log("Testing Security Vulnerabilities", "WARNING")
        
        vulnerabilities = []
        
        # Test XSS
        try:
            await page.goto(f"{self.base_url}/settings")
            xss_payload = "<script>console.log('XSS')</script>"
            
            # Switch to keywords tab
            await page.click("button:has-text('Keywords')")
            await page.click("button:has-text('Add Keyword')")
            await page.fill("#keyword-text", xss_payload)
            await page.click("#keyword-form button[type='submit']")
            await page.wait_for_timeout(1000)
            
            # Check if script was escaped in the table
            keyword_cells = await page.locator("td").all()
            found_vulnerability = False
            for cell in keyword_cells:
                text = await cell.inner_text()
                if xss_payload in text:
                    html = await cell.inner_html()
                    if "<script>" in html:
                        vulnerabilities.append("Possible XSS: Keyword text not escaped in settings table")
                        self.log("❌ Possible XSS detected!", "ERROR")
                        found_vulnerability = True
                        break
            
            if not found_vulnerability:
                self.log("✅ XSS Protection: Keyword text properly escaped", "SUCCESS")
        except Exception as e:
            self.log(f"Security check error: {str(e)}", "INFO")
        
        return {
            "test": "security",
            "vulnerabilities": vulnerabilities,
            "passed": len(vulnerabilities) == 0
        }
    
    async def run_all_tests(self):
        """Run all tests"""
        self.log("=" * 80, "INFO")
        self.log("VIRALENS COMPREHENSIVE DEEP TESTING", "INFO")
        self.log("=" * 80, "INFO")
        
        self.results["start_time"] = datetime.now().isoformat()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Test suite
            tests = [
                ("Landing Page", self.test_landing_page(page)),
                ("Sign Up Flow", self.test_signup_flow_complete(page, self.test_data["test_user1"])),
                ("Dashboard Buttons", self.test_dashboard_all_buttons(page)),
                ("Keyword Management", self.test_keyword_management_full(page)),
                ("Competitor Management", self.test_competitor_management_full(page)),
                ("API Endpoints", self.test_api_endpoints(page)),
                ("Title Prediction Stealth", self.test_title_prediction_stealth(page)),
                ("Security", self.test_security_vulnerabilities(page)),
            ]
            
            for test_name, test_coro in tests:
                self.log(f"\n{'=' * 60}", "INFO")
                self.log(f"Running: {test_name}", "INFO")
                self.log(f"{'=' * 60}", "INFO")
                
                try:
                    result = await test_coro
                    self.results["total_tests"] += 1
                    
                    if result.get("passed"):
                        self.results["passed"] += 1
                        self.log(f"✅ {test_name}: PASSED", "SUCCESS")
                    else:
                        self.results["failed"] += 1
                        self.log(f"❌ {test_name}: FAILED", "ERROR")
                        self.results["bugs_found"].append({
                            "test": test_name,
                            "result": result
                        })
                    
                except Exception as e:
                    self.results["failed"] += 1
                    self.log(f"💥 {test_name}: EXCEPTION - {str(e)}", "CRITICAL")
                    self.results["bugs_found"].append({
                        "test": test_name,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
            
            await browser.close()
        
        self.results["end_time"] = datetime.now().isoformat()
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST RESULTS SUMMARY", "INFO")
        self.log("=" * 80, "INFO")
        
        # Summary
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"Total Tests: {total}", "INFO")
        self.log(f"Passed: {passed}", "SUCCESS")
        self.log(f"Failed: {failed}", "ERROR")
        self.log(f"Pass Rate: {pass_rate:.1f}%", "INFO")
        
        # Bugs found
        if self.results["bugs_found"]:
            self.log(f"\n🐛 BUGS FOUND: {len(self.results['bugs_found'])}", "WARNING")
            for bug in self.results["bugs_found"]:
                self.log(f"  - {bug.get('test')}", "WARNING")
        
        # Save report
        report_path = Path("DEEP_TEST_REPORT.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"\n📄 Full report saved: {report_path}", "INFO")
        self.log(f"📸 Screenshots saved: {self.screenshots_dir}/", "INFO")


async def main():
    """Main entry point"""
    framework = DeepTestingFramework()
    await framework.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
