# VIRALENS ADMIN PANEL - USER GUIDE

Welcome to the VIRALENS Admin Panel. This guide provides instructions on how to manage users, approvals, system settings, and more.

## Table of Contents
1. [Accessing the Admin Panel](#accessing-the-admin-panel)
2. [User Approval Workflow](#user-approval-workflow)
3. [Managing Users](#managing-users)
4. [Using Bulk Actions](#using-bulk-actions)
5. [Audit Logs & Security](#audit-logs--security)
6. [System Analytics](#system-analytics)
7. [System Settings](#system-settings)
8. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## 1. Accessing the Admin Panel
To access the admin panel:
1. Navigate to your VIRALENS application URL.
2. Go to `/admin` (e.g., `http://your-domain.com/admin`).
3. If you are not logged in, you will be prompted to enter your admin credentials.
4. Once authenticated, you will see the **Admin Dashboard** with high-level statistics.

### Resetting Admin Password
If you lose your admin password or need to update it, use the provided utility script. From the project root, run:

```bash
python3 scripts/update_admin.py YourNewPassword123!
```

> [!NOTE]
> The password must be at least 8 characters long and include one uppercase letter and one number.

---

## 2. User Approval Workflow
VIRALENS uses a semi-automated onboarding process where new users may require manual approval.

### Viewing Pending Users
1. From the sidebar, click on **Pending Approvals**.
2. This screen shows all users who have signed up but have not yet been approved.

### Approving or Rejecting a User
- **To Approve**: Click the green **Approve** button next to a user. They will receive access immediately.
- **To Reject**: Click the red **Reject** button. You may be prompted to provide a reason for the rejection (optional).

---

## 3. Managing Users
The **Users** page allows you to search, filter, and manage all registered accounts.

- **Search**: Use the search bar to find users by email or username.
- **Filter**: Filter users by **Subscription Tier** (Free/Pro) or **Status** (Active/Suspended/Pending).
- **User Detail**: Click on a user's name or the **View** button to see their full profile, research history, and admin notes.

---

## 4. Using Bulk Actions
Bulk actions allow you to perform tasks on multiple users simultaneously.

1. Go to the **Users** or **Pending Approvals** page.
2. Select users by clicking the checkboxes on the left side of the table.
3. Once one or more users are selected, the **Bulk Actions Toolbar** will appear at the bottom of the screen.
4. Select an action:
   - **Approve Selected**: Approve all selected pending users.
   - **Suspend Selected**: Block access for selected users.
   - **Activate Selected**: Restore access for suspended users.
   - **Export Selected**: Download a CSV file containing details of the selected users.
   - **Delete Selected**: Permanently remove the selected accounts (use with caution).

---

## 5. Audit Logs & Security
Every administrative action is tracked for security and compliance.

1. Navigate to **Audit Logs**.
2. Here you can see:
   - **Who** performed the action.
   - **What** action was performed (e.g., "User Approved", "Settings Updated").
   - **Target**: Which user or system component was affected.
   - **Timestamp**: Exactly when it happened.
3. Use the filters to find specific events or investigate suspicious activity.

---

## 6. System Analytics
The **Analytics** page provides visual insights into system performance.

- **User Growth**: Real-time chart showing new signups over the last 7, 30, or 90 days.
- **Research Activity**: Tracks the number of research runs performed by users.
- **Top Users**: A leaderboard of the most active participants.
- **Exporting**: Click **Export PDF** to generate a professional report for stakeholder review.

---

## 7. System Settings
Control the behavior of the entire VIRALENS platform from the **Settings** page.

- **General**: Site name, support email, and basic configuration.
- **Security**: Password policies, session timeouts, and admin access controls.
- **Email (SMTP)**: Configure the mail server for system notifications (Approvals/Reset Passwords).
- **API (Advanced)**: Manage integration keys and system-level performance toggles like "Fail-fast" mode.

---

## 8. Troubleshooting & FAQ

### FAQ
**Q: Why can't a user log in after signing up?**
A: They are likely in "Pending" status. Check the **Pending Approvals** page and approve their account.

**Q: How do I change a user's subscription tier?**
A: Go to the **Users** page, click **View** on the specific user, and use the **Edit User** modal to change their tier.

**Q: Can I undo a bulk deletion?**
A: No. Deletions are permanent. We highly recommend using "Suspend" instead of "Delete" if you wish to temporarily block a user.

### Troubleshooting
- **Dashboard not loading**: Check your internet connection or contact technical support to ensure the database is online.
- **Search not working**: Ensure you are using the correct spelling for usernames or full email addresses.
- **Email notifications not sending**: Verify your SMTP settings in the **Settings > Email** tab.
