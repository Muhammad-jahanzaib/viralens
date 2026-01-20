# VIRALENS ADMIN PANEL - DEVELOPER HANDOFF

This document provides technical details for maintaining and extending the VIRALENS Admin Panel.

## 1. Architecture Overview
The Admin Panel is an extension of the main Flask application, separated by a Blueprint (`admin`) and protected by a custom decorator.

- **Backend**: Python 3.13, Flask, SQLAlchemy (ORM).
- **Frontend**: Jinja2 Templates, Vanilla JavaScript, Vanilla CSS.
- **Testing**: Playwright (Browser Automation).

---

## 2. Code Structure

### Blueprints & Routes
- `admin_routes.py`: Contains all 21 administrative routes.
- `@admin_required`: Custom decorator in `utils/admin_utils.py` that enforces admin-only access.

### Models (`models.py`)
- `User`: Extended with `approval_status`, `approved_by`, `approved_at`, `rejection_reason`.
- `AdminLog`: Tracks every mutation performed by an admin.
- `SystemSetting`: Key-VALUE store for application configurations.

### Templates
- `templates/admin/base_admin.html`: Master layout containing shared CSS/JS and navigation.
- `static/js/admin_bulk_actions.js`: Handles checkbox logic and AJAX requests for bulk operations.

---

## 3. Database Schema
The following tables are central to the Admin Panel:

| Table | Purpose | Key Columns |
| :--- | :--- | :--- |
| **users** | Core accounts | `approval_status` (pending/approved/rejected/suspended) |
| **admin_logs** | Audit Trail | `admin_id`, `action`, `target_id`, `details` |
| **system_settings** | Key-Value Config | `key`, `value`, `description`, `category` |

---

## 4. API Endpoints Reference
The Admin Panel exposes several JSON endpoints for the bulk actions UI:

- `POST /admin/api/users/bulk-approve`: Expects `{"user_ids": [...]}`
- `POST /admin/api/users/bulk-reject`: Expects `{"user_ids": [...], "reason": "..."}`
- `POST /admin/api/users/bulk-delete`: Destructive - remove users.

All API endpoints return JSON formats:
```json
{"success": true, "message": "Users approved successfully", "count": 5}
```

---

## 5. Testing Guide
The project uses a comprehensive Playwright automation suite.

### Running Tests
```bash
# Full suite (Headed)
python3 test_browser_automation.py

# Admin-only (Headless)
python3 test_browser_automation.py --headless --admin-only
```

### Key Test Concepts
- **Auto-Approval**: The `approve_test_user_as_admin` helper handles the approval block for new signups.
- **Screenshots**: Saved to `test_screenshots/` on any failure.
- **Fail-fast**: The suite will attempt to continue but logs critical failures immediately.

---

## 6. Deployment Checklist
1. **Migrations**: Apply `migration_add_approval.py` if adding to a new database.
2. **Admin Setup**: Use `scripts/reset_admin_password.py` to initialize the `admin@viralens.ai` account.
3. **Static Assets**: Ensure `static/js/admin_bulk_actions.js` is accessible.
4. **Permissions**: The web server must have write access to the database folder (for SQLite).

---

## 7. Maintenance Tasks
- **Log Rotation**: The `admin_logs` table can grow large. Consider a cleanup script for logs older than 12 months.
- **Settings Backup**: Important system configurations are stored in `system_settings`. Ensure these are part of your DB backup strategy.
- **Dependency Updates**: Monitor `Flask` and `SQLAlchemy` for security patches.

---

## 8. Known Limitations & Future Work
- **Email Stubs**: The email notification system in `admin_routes.py` uses placeholders. Integration with a real SMTP server is required for production notifications.
- **Search Latency**: The user search currently uses a basic `LIKE` query. For millions of users, consider implementing Elasticsearch or full-text indexing.
- **Concurrency**: The bulk delete operation does not currently implement a long-running task queue (like Celery). Deleting 10,000 users at once may timeout the request.

---

**Developed by:** Antigravity AI
**Final Release:** 1.0.0
**Project Status:** COMPLETE
