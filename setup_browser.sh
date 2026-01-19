#!/bin/bash

echo "=========================================="
echo "  🎭 BROWSER AUTOMATION SETUP"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found"

# Install Playwright
echo ""
echo "Step 1/3: Installing Playwright..."
pip3 install --quiet playwright pytest pytest-playwright

if [ $? -eq 0 ]; then
    echo "✅ Playwright installed"
else
    echo "❌ Playwright installation failed"
    exit 1
fi

# Install Chromium browser
echo ""
echo "Step 2/3: Installing Chromium browser (~200MB download)..."
playwright install chromium

if [ $? -eq 0 ]; then
    echo "✅ Chromium installed"
else
    echo "❌ Chromium installation failed"
    exit 1
fi

# Create screenshots directory
echo ""
echo "Step 3/3: Setting up directories..."
mkdir -p test_screenshots
echo "✅ Screenshots directory created"

echo ""
echo "=========================================="
echo "  ✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Quick Start:"
echo "1. Start server:  python3 app.py"
echo "2. Run tests:     python3 test_browser_automation.py"
echo "3. Watch tests:   python3 test_browser_automation.py --slow"
echo ""
echo "Screenshots will be saved to: test_screenshots/"
echo ""
