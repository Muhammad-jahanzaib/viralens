READY TO TEST - BULK ACTIONS
=============================
1. Pending Approvals page (/admin/users/pending)
   - Select multiple pending users with checkboxes
   - Click "Approve Selected" → should approve all
   - Click "Reject Selected" → prompt for reason, then reject

2. Users page (/admin/users)
   - Bulk actions toolbar should appear when users selected
   - Test suspend, activate, delete, export

3. Expected behavior:
   - Toast notification appears ("Processing...")
   - API call completes
   - Success toast appears with count
   - Page reloads after 1.5 seconds
   - Changes reflected in database

4. Verify in audit logs:
   - Go to Admin → Audit Logs
   - Check for bulk_approve, bulk_reject, bulk_suspend entries
