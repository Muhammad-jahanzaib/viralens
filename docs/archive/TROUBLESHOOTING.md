# Troubleshooting Guide

Common issues and solutions for Royal Research Automation.

## 1. Application Won't Start
**Symptom**: `Address already in use` error.
**Solution**:
-   Port 5000 is likely taken by MacOS Control Center (AirPlay).
-   Edit `app.py` line 521: change `port=5000` to `port=8000` or higher.
-   Or run with `flask run --port=8000`.

## 2. YouTube Data Missing
**Symptom**: Report says "Skipped (no competitors)" or YouTube shows 0 videos.
**Solution**:
-   Check **Settings** > **Competitors**. Are there valid active competitors?
-   Is `YOUTUBE_API_KEY` set correct in `.env`?
-   Did you hit your daily quota? (Free tier is 10,000 units/day). Check Google Cloud Console.

## 3. Twitter Collection Failing
**Symptom**: "403 Forbidden" or "429 Too Many Requests".
**Solution**:
-   Twitter API v2 Free Tier is very limited (only post creation or limited search).
-   If you have Basic/Pro access, ensure your `TWITTER_BEARER_TOKEN` is correct.
-   The current implementation uses `recent_search` which requires Basic Tier ($100/mo).
-   *Workaround*: Disable Twitter in code or accept failure in the report if on Free Tier.

## 4. AI Generation Errors
**Symptom**: "Claude AI generation failed".
**Solution**:
-   Check `ANTHROPIC_API_KEY`.
-   Check your credit balance at console.anthropic.com.
-   If the error is "Overloaded", wait a minute and try again.

## 5. Settings Not Saving
**Symptom**: Changes in UI disappear after restart.
**Solution**:
-   Check permissions of the folder where `competitors.json` is stored (`utils/` or `data/`).
-   Ensure the file is valid JSON (use a validator if editing manually).
-   The system keeps a `.bak` backup file; try restoring from that if the main file is corrupted.
