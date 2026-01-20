"""
Admin Routes for VIRALENS
Admin dashboard, user management, system monitoring
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
import json
from flask_login import login_required, current_user
from models import db, User, ResearchRun, TitlePerformance, AdminLog, SystemSettings, UserActivity
from utils.admin_utils import admin_required, log_admin_action, get_system_stats, get_user_stats, export_users_csv, export_research_runs_csv, send_system_email
from datetime import datetime, timedelta
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.context_processor
def inject_pending_count():
    """Inject pending user count into all admin templates"""
    count = User.query.filter_by(approval_status='pending').count()
    return dict(pending_count=count)


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard - main overview"""
    stats = get_system_stats()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Recent research runs
    recent_research = ResearchRun.query.order_by(ResearchRun.created_at.desc()).limit(10).all()
    
    # Recent admin logs
    recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(20).all()
    
    # System health
    health = {
        'database': 'healthy',
        'api': 'healthy',
        'storage': 'healthy'
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_research=recent_research,
                         recent_logs=recent_logs,
                         health=health)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search', '')
    tier_filter = request.args.get('tier', '')
    status_filter = request.args.get('status', '')
    
    # Build query
    query = User.query
    
    if search:
        query = query.filter(
            (User.email.contains(search)) |
            (User.username.contains(search)) |
            (User.full_name.contains(search))
        )
    
    if tier_filter:
        query = query.filter_by(subscription_tier=tier_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'admin':
        query = query.filter_by(is_admin=True)
    
    # Paginate
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html',
                         users=pagination.items,
                         pagination=pagination,
                         search=search,
                         tier_filter=tier_filter,
                         status_filter=status_filter)


@admin_bp.route('/users/pending')
@login_required
@admin_required
def users_pending():
    """Pending user approvals page"""
    # Get all pending users
    pending_users = User.query.filter_by(approval_status='pending').order_by(User.created_at.desc()).all()
    
    # Calculate statistics
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    approved_today = User.query.filter(
        User.approval_status == 'approved',
        User.approved_at >= today_start
    ).count()
    
    approved_this_week = User.query.filter(
        User.approval_status == 'approved',
        User.approved_at >= week_ago
    ).count()
    
    rejected_today = User.query.filter(
        User.approval_status == 'rejected',
        User.approved_at >= today_start  # approved_at is reused for rejection timestamp
    ).count()
    
    rejected_this_week = User.query.filter(
        User.approval_status == 'rejected',
        User.approved_at >= week_ago
    ).count()
    
    return render_template('admin/users_pending.html',
                         pending_users=pending_users,
                         pending_count=len(pending_users),
                         approved_today=approved_today,
                         approved_this_week=approved_this_week,
                         rejected_today=rejected_today,
                         rejected_this_week=rejected_this_week,
                         now=datetime.utcnow())


@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Approve a pending user"""
    try:
        user = User.query.get_or_404(user_id)
        
        if user.approval_status == 'pending':
            user.approval_status = 'approved'
            user.approved_by = current_user.id
            user.approved_at = datetime.utcnow()
            
            db.session.commit()
            
            send_system_email(
                user.email,
                "Your ViralLens Account is Approved! 🎉",
                "approval",
                user_id=user.id,
                name=user.full_name or user.username,
                tier=user.subscription_tier.capitalize()
            )
            
            log_admin_action(
                action='user_approve',
                target_type='user',
                target_id=user_id,
                description=f'Approved user {user.username}'
            )
            
            flash(f'✅ User {user.username} has been approved successfully.', 'success')
        else:
            flash(f'User {user.username} is not pending approval.', 'warning')
        
        return redirect(request.referrer or url_for('admin.users_pending'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving user: {str(e)}', 'danger')
        return redirect(url_for('admin.users_pending'))


@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    """Reject a pending user"""
    try:
        user = User.query.get_or_404(user_id)
        reason = request.form.get('reason', 'No reason provided')
        
        if user.approval_status == 'pending':
            user.approval_status = 'rejected'
            user.rejection_reason = reason
            user.approved_at = datetime.utcnow()  # Track when rejected
            
            db.session.commit()
            
            send_system_email(
                user.email,
                "Account Status Update - ViralLens",
                "rejection",
                user_id=user.id,
                name=user.full_name or user.username,
                reason=reason
            )
            
            log_admin_action(
                action='user_reject',
                target_type='user',
                target_id=user_id,
                description=f'Rejected user {user.username}. Reason: {reason}'
            )
            
            flash(f'❌ User {user.username} has been rejected.', 'success')
        else:
            flash(f'User {user.username} is not pending approval.', 'warning')
        
        return redirect(request.referrer or url_for('admin.users_pending'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting user: {str(e)}', 'danger')
        return redirect(url_for('admin.users_pending'))


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Detailed user view"""
    user_stats = get_user_stats(user_id)
    
    if not user_stats:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_detail.html', **user_stats)


@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details"""
    user = User.query.get_or_404(user_id)
    
    # Update fields
    user.email = request.form.get('email', user.email)
    user.username = request.form.get('username', user.username)
    user.full_name = request.form.get('full_name', user.full_name)
    user.niche = request.form.get('niche', user.niche)
    user.subscription_tier = request.form.get('subscription_tier', user.subscription_tier)
    user.subscription_status = request.form.get('subscription_status', user.subscription_status)
    user.is_active = request.form.get('is_active') == 'on'
    user.is_admin = request.form.get('is_admin') == 'on'
    
    # Reset password if provided
    new_password = request.form.get('new_password')
    if new_password:
        user.set_password(new_password)
    
    db.session.commit()
    
    log_admin_action(
        action='user_updated',
        target_type='User',
        target_id=user_id,
        description=f'Updated user {user.username}'
    )
    
    flash(f'User {user.username} updated successfully.', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend_user(user_id):
    """Suspend/unsuspend a user"""
    user = User.query.get_or_404(user_id)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = 'suspended' if not user.is_active else 'reactivated'
    
    if not user.is_active: # If user was just suspended
        send_system_email(
            user.email,
            "Account Suspended - ViralLens Security",
            "suspension",
            user_id=user.id,
            name=user.full_name or user.username
        )
    elif user.is_active: # If user was just reactivated
        send_system_email(
            user.email,
            "Account Reactivated - ViralLens",
            "reactivation",
            user_id=user.id,
            name=user.full_name or user.username
        )
    
    log_admin_action(
        action=f'user_{action}',
        target_type='User',
        target_id=user_id,
        description=f'{action.capitalize()} user {user.username}'
    )
    
    flash(f'User {user.username} has been {action}.', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user (soft delete by deactivating)"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the last admin user.', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    # Soft delete
    user.is_active = False
    user.email = f"deleted_{user.id}_{user.email}"
    user.username = f"deleted_{user.id}_{user.username}"
    db.session.commit()
    
    send_system_email(
        user.email,
        "Account Deletion Confirmation - ViralLens",
        "deletion",
        user_id=user.id,
        name=user.full_name or user.username
    )
    
    log_admin_action(
        action='user_deleted',
        target_type='User',
        target_id=user_id,
        description=f'Deleted user {user.username}'
    )
    
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/research-runs')
@login_required
@admin_required
def research_runs():
    """View all research runs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = ResearchRun.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    pagination = query.order_by(ResearchRun.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Calculate totals
    total_runtime = db.session.query(func.sum(ResearchRun.runtime_seconds)).scalar() or 0
    total_api_cost = db.session.query(func.sum(ResearchRun.api_cost)).scalar() or 0
    avg_runtime = db.session.query(func.avg(ResearchRun.runtime_seconds)).scalar() or 0
    
    return render_template('admin/research_runs.html',
                         runs=pagination.items,
                         pagination=pagination,
                         total_runtime=total_runtime,
                         total_api_cost=total_api_cost,
                         avg_runtime=avg_runtime,
                         user_id=user_id)


@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    """View admin audit logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action_filter = request.args.get('action', '')
    
    query = AdminLog.query
    
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    pagination = query.order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique actions for filter
    actions = db.session.query(AdminLog.action).distinct().all()
    actions = [a[0] for a in actions]
    
    return render_template('admin/logs.html',
                         logs=pagination.items,
                         pagination=pagination,
                         actions=actions,
                         action_filter=action_filter)


@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """System settings"""
    settings = SystemSettings.query.all()
    settings_dict = {s.key: s for s in settings}
    
    return render_template('admin/settings.html', settings=settings_dict)


@admin_bp.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """Update system settings"""
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            setting = SystemSettings.query.filter_by(key=setting_key).first()
            
            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
            else:
                setting = SystemSettings(
                    key=setting_key,
                    value=value
                )
                db.session.add(setting)
    
    db.session.commit()
    
    log_admin_action(
        action='settings_updated',
        description='Updated system settings'
    )
    
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('admin.settings'))


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analytics dashboard"""
    # User growth over time
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    user_growth = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(
        func.date(User.created_at)
    ).all()
    
    # Research runs per day
    research_activity = db.session.query(
        func.date(ResearchRun.created_at).label('date'),
        func.count(ResearchRun.id).label('count')
    ).filter(
        ResearchRun.created_at >= thirty_days_ago
    ).group_by(
        func.date(ResearchRun.created_at)
    ).all()
    
    # Top users by research runs
    top_users = db.session.query(
        User,
        func.count(ResearchRun.id).label('run_count')
    ).join(
        ResearchRun
    ).group_by(
        User.id
    ).order_by(
        desc('run_count')
    ).limit(10).all()
    
    # Process growth data to ensure consistent labels
    user_growth_processed = []
    for day in user_growth:
        dt = day.date
        label = str(dt)
        if isinstance(dt, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    d_obj = datetime.strptime(dt.split(' ')[0], fmt)
                    label = d_obj.strftime('%m/%d')
                    break
                except:
                    continue
        elif hasattr(dt, 'strftime'):
            label = dt.strftime('%m/%d')
        user_growth_processed.append({'label': label, 'count': day.count})

    research_activity_processed = []
    for day in research_activity:
        dt = day.date
        label = str(dt)
        if isinstance(dt, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    d_obj = datetime.strptime(dt.split(' ')[0], fmt)
                    label = d_obj.strftime('%m/%d')
                    break
                except:
                    continue
        elif hasattr(dt, 'strftime'):
            label = dt.strftime('%m/%d')
        research_activity_processed.append({'label': label, 'count': day.count})
    
    return render_template('admin/analytics.html',
                         user_growth=user_growth_processed,
                         research_activity=research_activity_processed,
                         top_users=top_users)


# ===== EXPORT ENDPOINTS =====

@admin_bp.route('/export/users')
@login_required
@admin_required
def export_users():
    """Export users as CSV"""
    csv_data = export_users_csv()
    
    log_admin_action(
        action='export_users',
        description='Exported users to CSV'
    )
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=viralens_users_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
    )


@admin_bp.route('/export/research-runs')
@login_required
@admin_required
def export_research():
    """Export research runs as CSV"""
    csv_data = export_research_runs_csv()
    
    log_admin_action(
        action='export_research_runs',
        description='Exported research runs to CSV'
    )
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=viralens_research_runs_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
    )


# ===== API ENDPOINTS FOR AJAX =====

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """Get system stats as JSON"""
    stats = get_system_stats()
    return jsonify(stats)


@admin_bp.route('/api/user/<int:user_id>/stats')
@login_required
@admin_required
def api_user_stats(user_id):
    """Get user stats as JSON"""
    user_stats = get_user_stats(user_id)
    
    if not user_stats:
        return jsonify({'error': 'User not found'}), 404
    
    # Convert objects to dicts
    result = {
        'user': {
            'id': user_stats['user'].id,
            'email': user_stats['user'].email,
            'username': user_stats['user'].username,
            'subscription_tier': user_stats['user'].subscription_tier,
        },
        'total_research_runs': user_stats['total_research_runs'],
        'research_runs_this_month': user_stats['research_runs_this_month'],
        'avg_runtime': float(user_stats['avg_runtime']),
        'total_api_cost': float(user_stats['total_api_cost']),
    }
    
    
    return jsonify(result)


# ==============================================
# BULK ACTIONS API ENDPOINTS
# ==============================================

@admin_bp.route('/api/users/bulk-approve', methods=['POST'])
@login_required
@admin_required
def bulk_approve_users():
    """Bulk approve pending users"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'}), 400
        
        approved_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user and user.approval_status == 'pending':
                user.approval_status = 'approved'
                user.approved_by = current_user.id
                user.approved_at = datetime.utcnow()
                approved_count += 1
                
                send_system_email(
                    user.email,
                    "Your ViralLens Account is Approved! 🎉",
                    "approval",
                    user_id=user.id,
                    name=user.full_name or user.username,
                    tier=user.subscription_tier.capitalize()
                )
        
        db.session.commit()
        
        log_admin_action(
            action='bulk_approve',
            target_type='users',
            target_id=None,
            description=f'Bulk approved {approved_count} users'
        )
        
        return jsonify({
            'success': True,
            'count': approved_count,
            'message': f'{approved_count} user(s) approved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/users/bulk-reject', methods=['POST'])
@login_required
@admin_required
def bulk_reject_users():
    """Bulk reject pending users"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        reason = data.get('reason', 'No reason provided')
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'}), 400
        
        rejected_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user and user.approval_status == 'pending':
                user.approval_status = 'rejected'
                user.rejection_reason = reason
                user.approved_at = datetime.utcnow()
                rejected_count += 1
                
                # TODO: Send rejection email
                # send_rejection_email(user, reason)
        
        db.session.commit()
        
        log_admin_action(
            action='bulk_reject',
            target_type='users',
            target_id=None,
            description=f'Bulk rejected {rejected_count} users. Reason: {reason}'
        )
        
        return jsonify({
            'success': True,
            'count': rejected_count,
            'message': f'{rejected_count} user(s) rejected'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/users/bulk-suspend', methods=['POST'])
@login_required
@admin_required
def bulk_suspend_users():
    """Bulk suspend users"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        reason = data.get('reason', 'Terms violation')
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'}), 400
        
        suspended_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user and user.is_active:
                user.is_active = False
                suspended_count += 1
                
                # TODO: Send suspension email
                # send_suspension_email(user, reason)
        
        db.session.commit()
        
        log_admin_action(
            action='bulk_suspend',
            target_type='users',
            target_id=None,
            description=f'Bulk suspended {suspended_count} users. Reason: {reason}'
        )
        
        return jsonify({
            'success': True,
            'count': suspended_count,
            'message': f'{suspended_count} user(s) suspended'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/users/bulk-activate', methods=['POST'])
@login_required
@admin_required
def bulk_activate_users():
    """Bulk activate suspended users"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'}), 400
        
        activated_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user and not user.is_active:
                user.is_active = True
                activated_count += 1
                
                # TODO: Send reactivation email
                # send_reactivation_email(user)
        
        db.session.commit()
        
        log_admin_action(
            action='bulk_activate',
            target_type='users',
            target_id=None,
            description=f'Bulk activated {activated_count} users'
        )
        
        return jsonify({
            'success': True,
            'count': activated_count,
            'message': f'{activated_count} user(s) activated'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/users/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_users():
    """Bulk delete users (soft delete)"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'}), 400
        
        # Prevent deleting admin users
        admin_ids = [u.id for u in User.query.filter_by(is_admin=True).all()]
        user_ids = [uid for uid in user_ids if uid not in admin_ids]
        
        deleted_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                user.is_active = False
                user.email = f"deleted_{user.id}_{user.email}"
                user.username = f"deleted_{user.id}_{user.username}"
                deleted_count += 1
        
        db.session.commit()
        
        log_admin_action(
            action='bulk_delete',
            target_type='users',
            target_id=None,
            description=f'Bulk deleted {deleted_count} users'
        )
        
        return jsonify({
            'success': True,
            'count': deleted_count,
            'message': f'{deleted_count} user(s) deleted'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/users/bulk-export', methods=['POST'])
@login_required
@admin_required
def bulk_export_users():
    """Export selected users as CSV"""
    try:
        data = request.form
        user_ids = json.loads(data.get('user_ids', '[]'))
        
        if not user_ids:
            flash('No users selected for export', 'error')
            return redirect(request.referrer or url_for('admin.users'))
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        # Generate CSV
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Tier', 'Status', 'Approval', 'Joined', 'Last Login', 'Research Runs'])
        
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.full_name or '',
                user.subscription_tier,
                'Active' if user.is_active else 'Suspended',
                user.approval_status if hasattr(user, 'approval_status') else 'N/A',
                user.created_at.strftime('%Y-%m-%d') if user.created_at else '',
                user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never',
                user.total_research_runs
            ])
        
        output.seek(0)
        
        log_admin_action(
            action='bulk_export',
            target_type='users',
            target_id=None,
            description=f'Exported {len(users)} selected users'
        )
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=viralens_selected_users_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(request.referrer or url_for('admin.users'))


@admin_bp.route('/api/research-runs/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_runs():
    """Bulk delete research runs"""
    try:
        data = request.get_json()
        run_ids = data.get('run_ids', [])
        
        if not run_ids:
            return jsonify({'success': False, 'message': 'No runs selected'}), 400
        
        deleted_count = ResearchRun.query.filter(ResearchRun.id.in_(run_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        log_admin_action(
            action='bulk_delete_runs',
            target_type='research_runs',
            target_id=None,
            description=f'Bulk deleted {deleted_count} research runs'
        )
        
        return jsonify({
            'success': True,
            'count': deleted_count,
            'message': f'{deleted_count} research run(s) deleted'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
