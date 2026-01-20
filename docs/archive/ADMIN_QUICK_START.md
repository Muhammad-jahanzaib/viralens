# 🚀 Admin Panel Quick Start Guide

Welcome to the **ViralLens Admin Panel**! This guide will get you up and running in minutes.

## 1. Start the Application

Open your terminal, navigate to the project directory, and start the Flask server:

```bash
cd ~/royal-research-automation
python3 app.py
```

You should see output similar to:
```
* Running on http://127.0.0.1:8000
* Debug mode: on
```

## 2. Login as Administrator

1.  Open your browser and go to: [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
2.  Enter the default admin credentials:
    *   **Email**: `admin@viralens.ai`
    *   **Password**: `Admin123!@#`

> **Note**: If you created the admin user manually with a different password, use that instead.

## 3. Access the Admin Panel

Once logged in, you have two ways to access the Admin Panel:

1.  **Navigation Bar**: Click the gold **"🛡️ Admin Panel"** button in the top navigation bar (next to "App Dashboard").
2.  **Direct URL**: Navigate to [http://127.0.0.1:8000/admin/dashboard](http://127.0.0.1:8000/admin/dashboard)

## 4. Admin Features Overview

The Admin Panel provides comprehensive control over the ViralLens platform:

*   **📊 Dashboard**: Real-time overview of system stats (users, active sessions, research runs) and recent activity.
*   **👥 User Management**:
    *   View all registered users.
    *   Filter by Subscription Tier (Free/Pro/Agency) or Status.
    *   Edit user profiles, upgrade/downgrade tiers.
    *   Suspend or Deactivate users.
    *   Soft-delete users (removes PII but keeps historical data).
*   **🔬 Research Monitoring**:
    *   View global research run history.
    *   Monitor API usage and costs per run.
    *   Inspect generated topics and keywords.
*   **📋 Audit Logs**:
    *   Full traceability of all admin actions.
    *   Filter logs by action type (e.g., `user_suspended`, `settings_updated`).
    *   Track IP addresses and timestamps.
*   **⚙️ System Settings**:
    *   **Email Config**: SMTP server settings for notifications.
    *   **API Keys**: Manage YouTube and Google Search API keys centrally.
    *   **Feature Toggles**: Enable/disable signups, maintenance mode, etc.
    *   **Limits**: Set monthly research limits for each subscription tier.
*   **📈 Analytics**:
    *   Visual charts for User Growth and Research Activity (last 30 days).
    *   Top active users leaderboard.
*   **📥 Data Export**:
    *   Export Users list to CSV.
    *   Export Research Runs history to CSV.

## 5. Troubleshooting

### Option "Admin Panel" link is missing
*   **Cause**: Your user account does not have the `is_admin` flag set to `True`.
*   **Fix**: Run the following python script to promote your user:
    ```python
    from app import app, db
    from models import User
    with app.app_context():
        u = User.query.filter_by(email='your_email@example.com').first()
        u.is_admin = True
        db.session.commit()
    ```

### "Access Denied" when visiting /admin
*   **Cause**: You are either not logged in, or logged in as a regular user.
*   **Fix**: Log out and log back in as `admin@viralens.ai`.

### Database Errors (OperationalError, no such table)
*   **Cause**: Database schema hasn't been updated with new admin tables.
*   **Fix**: Run the migration script provided in `ANTIGRAVITY_STEP_BY_STEP.md`.

## 6. Security Checklist 🔒

Before deploying to production, ensure you complete these steps:

- [ ] **Change Default Password**: Immediately change the password for `admin@viralens.ai`.
- [ ] **HTTPS**: Ensure your production server uses HTTPS to protect admin sessions.
- [ ] **Secret Key**: Set a strong `SECRET_KEY` environment variable.
- [ ] **Backup**: Regularly backup your `viralens.db` database.

## 7. Next Steps

*   Explore the **Analytics** tab to understand user behavior.
*   Configure your **SMTP settings** to enable system emails.
*   Set appropriate **Research Limits** based on your API quotas.

---
**ViralLens Admin Panel**
Est. 2026
