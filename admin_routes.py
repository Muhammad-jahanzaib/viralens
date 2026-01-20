"""
Admin Routes for VIRALENS
Admin dashboard, user management, system monitoring
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from models import db, User, ResearchRun, TitlePerformance, AdminLog, SystemSettings, UserActivity
from utils.admin_utils import admin_required, log_admin_action, get_system_stats, get_user_stats, export_users_csv, export_research_runs_csv
from datetime import datetime, timedelta
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


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
    
    return render_template('admin/analytics.html',
                         user_growth=user_growth,
                         research_activity=research_activity,
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
