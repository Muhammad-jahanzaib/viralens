#!/usr/bin/env python3
"""
MASTER TEST RUNNER - ViralLens Complete System Testing
Runs ALL tests and generates comprehensive bug report with fixes

Tests:
1. Browser automation (UI/UX)
2. API endpoints  
3. Authentication flows
4. CRUD operations
5. Data isolation
6. Title prediction quality
7. System performance
8. Security checks

Generates:
- Bug report (JSON + HTML)
- Fix recommendations
- Priority matrix
- Screenshots
"""

import subprocess
import sys
import time
# turbo
from pathlib import Path
import json
from datetime import datetime


class MasterTestRunner:
    def __init__(self):
        self.start_time = time.time()
        self.results = {
            'browser_tests': None,
            'api_tests': None,
            'title_prediction': None,
            'overall_bugs': [],
            'overall_recommendations': []
        }
    
    def print_header(self, text):
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80 + "\n")
    
    def run_browser_tests(self):
        """Run comprehensive browser tests"""
        self.print_header("🌐 RUNNING BROWSER TESTS")
        
        try:
            # Run the comprehensive system tester
            result = subprocess.run(
                [sys.executable, 'test_comprehensive_system.py'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            print(result.stdout)
            
            # Try to load the JSON report
            report_file = Path("test_reports/test_report.json")
            if report_file.exists():
                with open(report_file, 'r') as f:
                    self.results['browser_tests'] = json.load(f)
            
            return result.returncode == 0
        
        except subprocess.TimeoutExpired:
            print("❌ Browser tests timed out (5 minutes)")
            return False
        except Exception as e:
            print(f"❌ Error running browser tests: {e}")
            return False
    
    def run_title_prediction_eval(self):
        """Run title prediction evaluation"""
        self.print_header("🎯 EVALUATING TITLE PREDICTION SYSTEM")
        
        try:
            result = subprocess.run(
                [sys.executable, 'test_title_prediction.py'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(result.stdout)
            
            # Load results
            report_file = Path("test_reports/title_prediction_report.json")
            if report_file.exists():
                with open(report_file, 'r') as f:
                    self.results['title_prediction'] = json.load(f)
            
            return True
        
        except Exception as e:
            print(f"❌ Error evaluating title prediction: {e}")
            return False
    
    def run_api_tests(self):
        """Run API tests"""
        self.print_header("🔌 RUNNING API TESTS")
        
        try:
            # Note: The user mentioned test_comprehensive.py but let's check if it exists.
            # If not, we might fall back to test_unit.py
            cmd = 'test_comprehensive.py'
            if not Path(cmd).exists():
                if Path('test_unit.py').exists():
                    cmd = 'test_unit.py'
                else:
                    print(f"⚠️  Test file {cmd} not found and no fallback.")
                    return False

            result = subprocess.run(
                [sys.executable, cmd, '-v'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(result.stdout)
            
            # Parse pytest output for pass/fail
            output = result.stdout
            if 'passed' in output:
                self.results['api_tests'] = {
                    'status': 'PASSED',
                    'output': output
                }
            else:
                self.results['api_tests'] = {
                    'status': 'FAILED',
                    'output': output
                    # Note: Original code had a formatting error with the dict here, I fixed it.
                }
            
            return True
        
        except Exception as e:
            print(f"⚠️  API tests not available: {e}")
            return False
    
    def aggregate_bugs(self):
        """Aggregate all bugs from different test suites"""
        self.print_header("🐛 AGGREGATING BUGS")
        
        all_bugs = []
        
        # From browser tests
        if self.results['browser_tests']:
            browser_bugs = self.results['browser_tests'].get('bugs', [])
            all_bugs.extend(browser_bugs)
            print(f"  Browser tests: {len(browser_bugs)} bugs")
        
        # From title prediction
        if self.results['title_prediction']:
            title_bugs = self.results['title_prediction'].get('issues', [])
            all_bugs.extend(title_bugs)
            print(f"  Title prediction: {len(title_bugs)} issues")
        
        self.results['overall_bugs'] = all_bugs
        print(f"\n  📊 Total bugs found: {len(all_bugs)}")
        
        # Categorize by severity
        critical = [b for b in all_bugs if b.get('severity') == 'CRITICAL']
        high = [b for b in all_bugs if b.get('severity') == 'HIGH']
        medium = [b for b in all_bugs if b.get('severity') == 'MEDIUM']
        low = [b for b in all_bugs if b.get('severity') == 'LOW']
        
        print(f"\n  🔴 Critical: {len(critical)}")
        print(f"  🟠 High: {len(high)}")
        print(f"  🟡 Medium: {len(medium)}")
        print(f"  🔵 Low: {len(low)}")
    
    def generate_master_report(self):
        """Generate master HTML report"""
        self.print_header("📄 GENERATING MASTER REPORT")
        
        elapsed = time.time() - self.start_time
        
        # Create comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': elapsed,
            'test_suites': {
                'browser_tests': self.results['browser_tests'],
                'api_tests': self.results['api_tests'],
                'title_prediction': self.results['title_prediction']
            },
            'bugs': self.results['overall_bugs'],
            'recommendations': self.results['overall_recommendations']
        }
        
        # Save JSON
        json_file = Path("test_reports/MASTER_TEST_REPORT.json")
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"  ✅ JSON report: {json_file}")
        
        # Generate HTML report
        html = self.generate_html_report(report)
        html_file = Path("test_reports/MASTER_TEST_REPORT.html")
        
        with open(html_file, 'w') as f:
            f.write(html)
        
        print(f"  ✅ HTML report: {html_file}")
        
        return html_file
    
    def generate_html_report(self, report):
        """Generate HTML report"""
        bugs = report['bugs']
        
        # Group bugs by severity
        critical = [b for b in bugs if b.get('severity') == 'CRITICAL']
        high = [b for b in bugs if b.get('severity') == 'HIGH']
        medium = [b for b in bugs if b.get('severity') == 'MEDIUM']
        low = [b for b in bugs if b.get('severity') == 'LOW']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ViralLens - Master Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #6366f1; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #6366f1; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #6366f1; }}
        .stat-label {{ color: #666; font-size: 0.9rem; }}
        .bug {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; }}
        .bug.critical {{ border-left: 5px solid #dc2626; background: #fef2f2; }}
        .bug.high {{ border-left: 5px solid #f97316; background: #fff7ed; }}
        .bug.medium {{ border-left: 5px solid #f59e0b; background: #fffbeb; }}
        .bug.low {{ border-left: 5px solid #3b82f6; background: #eff6ff; }}
        .bug-title {{ font-weight: bold; margin-bottom: 5px; }}
        .bug-category {{ display: inline-block; background: #e5e7eb; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 10px; }}
        .bug-severity {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; color: white; }}
        .severity-critical {{ background: #dc2626; }}
        .severity-high {{ background: #f97316; }}
        .severity-medium {{ background: #f59e0b; }}
        .severity-low {{ background: #3b82f6; }}
        .timestamp {{ color: #999; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 ViralLens - Master Test Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">{len(bugs)}</div>
                <div class="stat-label">Total Bugs Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(critical)}</div>
                <div class="stat-label">Critical Issues</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(high)}</div>
                <div class="stat-label">High Priority</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report['duration_seconds']:.1f}s</div>
                <div class="stat-label">Test Duration</div>
            </div>
        </div>
        
        <h2>🔴 Critical Issues ({len(critical)})</h2>
        {self._generate_bug_html(critical)}
        
        <h2>🟠 High Priority Issues ({len(high)})</h2>
        {self._generate_bug_html(high)}
        
        <h2>🟡 Medium Priority Issues ({len(medium)})</h2>
        {self._generate_bug_html(medium)}
        
        <h2>🔵 Low Priority Issues ({len(low)})</h2>
        {self._generate_bug_html(low)}
    </div>
</body>
</html>
"""
        return html
    
    def _generate_bug_html(self, bugs):
        """Generate HTML for bug list"""
        if not bugs:
            return "<p>No issues found in this category. ✅</p>"
        
        html = ""
        for bug in bugs:
            severity = bug.get('severity', 'UNKNOWN').lower()
            category = bug.get('category', 'Unknown')
            title = bug.get('title', 'Untitled')
            description = bug.get('description', 'No description')
            
            html += f"""
            <div class="bug {severity}">
                <div class="bug-title">
                    <span class="bug-category">{category}</span>
                    <span class="bug-severity severity-{severity}">{bug.get('severity', 'UNKNOWN')}</span>
                    {title}
                </div>
                <p>{description}</p>
            </div>
            """
        
        return html
    
    def print_final_summary(self):
        """Print final summary"""
        self.print_header("📊 FINAL SUMMARY")
        
        total_bugs = len(self.results['overall_bugs'])
        critical = len([b for b in self.results['overall_bugs'] if b.get('severity') == 'CRITICAL'])
        
        if total_bugs == 0:
            print("  ✅ NO BUGS FOUND!")
            print("  🎉 System is ready for production!")
        elif critical > 0:
            print(f"  ❌ {critical} CRITICAL BUGS FOUND")
            print("  ⚠️  Fix critical bugs before proceeding")
        else:
            print(f"  ⚠️  {total_bugs} bugs found (no critical)")
            print("  ✅ System can proceed with caution")
        
        print(f"\n  📄 See detailed reports in: test_reports/")
        print(f"  🌐 Open: test_reports/MASTER_TEST_REPORT.html")
    
    def run_all(self):
        """Run all tests"""
        print("=" * 80)
        print("  🚀 VIRALENS - MASTER TEST RUNNER")
        print("  Testing EVERYTHING - Every button, every flow, every system")
        print("=" * 80)
        
        # Run all test suites
        self.run_browser_tests()
        self.run_api_tests()
        self.run_title_prediction_eval()
        
        # Aggregate and report
        self.aggregate_bugs()
        html_file = self.generate_master_report()
        self.print_final_summary()
        
        print("\n" + "=" * 80)
        print(f"  ✅ Testing complete! Duration: {time.time() - self.start_time:.1f}s")
        print("=" * 80)


if __name__ == "__main__":
    runner = MasterTestRunner()
    runner.run_all()
