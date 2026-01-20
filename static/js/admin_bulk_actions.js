// ==============================================
// ADMIN BULK ACTIONS
// Handles bulk selection and actions for admin tables
// ==============================================

document.addEventListener('DOMContentLoaded', function () {
    // Initialize bulk actions for users tables
    if (document.querySelector('.user-checkbox')) {
        setupBulkSelection(
            '.user-checkbox',
            '#select-all-users',
            '#bulk-actions-toolbar',
            '#selected-count'
        );
    }

    // Initialize bulk actions for research runs (if exists)
    if (document.querySelector('.run-checkbox')) {
        setupBulkSelection(
            '.run-checkbox',
            '#select-all-runs',
            '#bulk-runs-toolbar',
            '#runs-selected-count'
        );
    }
});

// ==============================================
// SELECTION MANAGEMENT
// ==============================================

function setupBulkSelection(checkboxClass, selectAllId, toolbarId, counterId) {
    const selectAll = document.querySelector(selectAllId);
    const checkboxes = document.querySelectorAll(checkboxClass);
    const toolbar = document.querySelector(toolbarId);
    const counter = document.querySelector(counterId);

    if (!selectAll || checkboxes.length === 0) return;

    // Select all functionality
    selectAll.addEventListener('change', function () {
        checkboxes.forEach(cb => cb.checked = this.checked);
        updateSelectionUI(checkboxes, toolbar, counter);
    });

    // Individual checkbox functionality
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function () {
            updateSelectionUI(checkboxes, toolbar, counter);
            // Update select-all checkbox state
            const allChecked = Array.from(checkboxes).every(c => c.checked);
            const someChecked = Array.from(checkboxes).some(c => c.checked);
            if (selectAll) {
                selectAll.checked = allChecked;
                selectAll.indeterminate = someChecked && !allChecked;
            }
        });
    });
}

function updateSelectionUI(checkboxes, toolbar, counter) {
    const selectedCount = Array.from(checkboxes).filter(cb => cb.checked).length;

    if (selectedCount > 0) {
        if (toolbar) toolbar.style.display = 'flex';
        if (counter) counter.textContent = `${selectedCount} item${selectedCount > 1 ? 's' : ''} selected`;
    } else {
        if (toolbar) toolbar.style.display = 'none';
    }
}

function getSelectedIds(checkboxClass) {
    const checkboxes = document.querySelectorAll(checkboxClass + ':checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.dataset.userId || cb.dataset.runId));
}

// ==============================================
// BULK ACTIONS - USERS
// ==============================================

function bulkApprove() {
    const userIds = getSelectedIds('.user-checkbox');
    if (userIds.length === 0) {
        showToast('No users selected', 'error');
        return;
    }

    if (confirm(`Approve ${userIds.length} user(s)?`)) {
        makeAPICall('/admin/api/users/bulk-approve', 'POST', { user_ids: userIds }, function (response) {
            showToast(response.message || 'Users approved successfully', 'success');
            setTimeout(() => location.reload(), 1500);
        });
    }
}

function bulkReject() {
    const userIds = getSelectedIds('.user-checkbox');
    if (userIds.length === 0) {
        showToast('No users selected', 'error');
        return;
    }

    const reason = prompt('Enter rejection reason:');
    if (reason && reason.trim()) {
        makeAPICall('/admin/api/users/bulk-reject', 'POST',
            { user_ids: userIds, reason: reason },
            function (response) {
                showToast(response.message || 'Users rejected', 'success');
                setTimeout(() => location.reload(), 1500);
            }
        );
    }
}

function bulkSuspend() {
    const userIds = getSelectedIds('.user-checkbox');
    if (userIds.length === 0) {
        showToast('No users selected', 'error');
        return;
    }

    const reason = prompt('Enter suspension reason:');
    if (reason && confirm(`Suspend ${userIds.length} user(s)?`)) {
        makeAPICall('/admin/api/users/bulk-suspend', 'POST',
            { user_ids: userIds, reason: reason },
            function (response) {
                showToast(response.message || 'Users suspended', 'success');
                setTimeout(() => location.reload(), 1500);
            }
        );
    }
}

function bulkActivate() {
    const userIds = getSelectedIds('.user-checkbox');
    if (userIds.length === 0) {
        showToast('No users selected', 'error');
        return;
    }

    if (confirm(`Activate ${userIds.length} user(s)?`)) {
        makeAPICall('/admin/api/users/bulk-activate', 'POST', { user_ids: userIds }, function (response) {
            showToast(response.message || 'Users activated', 'success');
            setTimeout(() => location.reload(), 1500);
        });
    }
}

function bulkDelete() {
    const userIds = getSelectedIds('.user-checkbox');
    if (userIds.length === 0) {
        showToast('No users selected', 'error');
        return;
    }

    if (confirm(`⚠️ WARNING: Delete ${userIds.length} user(s)? This action cannot be undone.`)) {
        makeAPICall('/admin/api/users/bulk-delete', 'POST', { user_ids: userIds }, function (response) {
            showToast(response.message || 'Users deleted', 'success');
            setTimeout(() => location.reload(), 1500);
        });
    }
}

function bulkExport() {
    const userIds = getSelectedIds('.user-checkbox');
    if (userIds.length === 0) {
        showToast('No users selected', 'error');
        return;
    }

    // Create hidden form and submit
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/admin/api/users/bulk-export';
    form.style.display = 'none';

    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'user_ids';
    input.value = JSON.stringify(userIds);
    form.appendChild(input);

    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);

    showToast('Export started...', 'success');
}

// ==============================================
// INDIVIDUAL USER ACTIONS
// ==============================================

function approveUser(userId) {
    if (confirm('Approve this user?')) {
        window.location.href = `/admin/users/${userId}/approve`;
    }
}

function rejectUser(userId) {
    const reason = prompt('Enter rejection reason:');
    if (reason && reason.trim()) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/users/${userId}/reject`;
        form.style.display = 'none';

        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'reason';
        input.value = reason;
        form.appendChild(input);

        document.body.appendChild(form);
        form.submit();
    }
}

function suspendUser(userId) {
    const reason = prompt('Enter suspension reason:');
    if (reason && confirm('Suspend this user?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/users/${userId}/suspend`;
        form.style.display = 'none';

        const reasonInput = document.createElement('input');
        reasonInput.type = 'hidden';
        reasonInput.name = 'reason';
        reasonInput.value = reason;
        form.appendChild(reasonInput);

        document.body.appendChild(form);
        form.submit();
    }
}

function deleteUser(userId) {
    if (confirm('⚠️ WARNING: Delete this user? This action cannot be undone.')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/users/${userId}/delete`;
        form.style.display = 'none';

        document.body.appendChild(form);
        form.submit();
    }
}

function saveAdminNotes(userId) {
    const notes = document.getElementById('admin-notes').value;

    makeAPICall(`/admin/users/${userId}/save-notes`, 'POST', { notes: notes }, function (response) {
        showToast('Notes saved successfully', 'success');
    });
}

// ==============================================
// UTILITY FUNCTIONS
// ==============================================

function makeAPICall(url, method, data, successCallback) {
    showToast('Processing...', 'info');

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                successCallback(data);
            } else {
                showToast(data.message || 'Operation failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Network error occurred', 'error');
        });
}

function showToast(message, type = 'info') {
    // Remove any existing toasts
    const existingToast = document.querySelector('.toast');
    if (existingToast) existingToast.remove();

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Style toast
    Object.assign(toast.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 25px',
        borderRadius: '8px',
        zIndex: '9999',
        fontWeight: '600',
        fontSize: '14px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        animation: 'slideIn 0.3s ease-out'
    });

    // Type-specific styling
    const colors = {
        success: { bg: '#10b981', color: 'white' },
        error: { bg: '#ef4444', color: 'white' },
        warning: { bg: '#f59e0b', color: 'white' },
        info: { bg: '#3b82f6', color: 'white' }
    };

    const colorScheme = colors[type] || colors.info;
    toast.style.backgroundColor = colorScheme.bg;
    toast.style.color = colorScheme.color;

    document.body.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add CSS animation
if (!document.querySelector('#toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(400px); opacity: 0; }
        }
        .bulk-toolbar {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px 20px;
            background: #f8fafc;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 2px solid #e2e8f0;
        }
        .bulk-toolbar #selected-count {
            font-weight: 600;
            color: #475569;
            margin-right: auto;
        }
        .btn-success { background: #10b981; }
        .btn-danger { background: #ef4444; }
        .btn-warning { background: #f59e0b; }
        .btn-primary { background: #3b82f6; }
        .btn-secondary { background: #64748b; }
        .btn-sm { 
            padding: 6px 12px;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-sm:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
    `;
    document.head.appendChild(style);
}

// ==============================================
// FILTERS & SEARCH
// ==============================================

function applyFilters() {
    const search = document.getElementById('search-users')?.value || '';
    const tier = document.getElementById('tier-filter')?.value || 'all';
    const status = document.getElementById('status-filter')?.value || 'all';
    const approval = document.getElementById('approval-filter')?.value || 'all';

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (tier && tier !== 'all') params.append('tier', tier);
    if (status && status !== 'all') params.append('status', status);
    if (approval && approval !== 'all') params.append('approval', approval);

    window.location.href = `?${params.toString()}`;
}

function clearFilters() {
    window.location.href = window.location.pathname;
}
