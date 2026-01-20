"""
Admin Utilities for VIRALENS
Decorators, helpers, and admin-specific functions
"""

from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user
from models import db, AdminLog, UserActivity
from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def log_admin_action(action, target_type=None, target_id=None, description=None):
    """Log an admin action for audit trail"""
    try:
        log = AdminLog(
            admin_id=current_user.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            description=description,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging admin action: {e}")


def log_user_activity(user_id, action, details=None):
    """Log user activity for analytics"""
    try:
        activity = UserActivity(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Error logging user activity: {e}")


def get_system_stats():
    """Get system-wide statistics"""
    from models import User, ResearchRun, TitlePerformance
    from sqlalchemy import func
    
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'total_research_runs': ResearchRun.query.count(),
        'research_runs_today': ResearchRun.query.filter(
            func.date(ResearchRun.created_at) == datetime.utcnow().date()
        ).count(),
        'total_title_performances': TitlePerformance.query.count(),
        
        # Subscription breakdown
        'free_users': User.query.filter_by(subscription_tier='free').count(),
        'pro_users': User.query.filter_by(subscription_tier='pro').count(),
        'agency_users': User.query.filter_by(subscription_tier='agency').count(),
        
        # Recent activity
        'new_users_this_week': User.query.filter(
            User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0) - timedelta(days=7)
        ).count() if 'timedelta' in dir() else 0,
    }
    
    return stats


def get_user_stats(user_id):
    """Get detailed stats for a specific user"""
    from models import User, ResearchRun, TitlePerformance
    from sqlalchemy import func
    
    user = User.query.get(user_id)
    if not user:
        return None
    
    stats = {
        'user': user,
        'total_research_runs': ResearchRun.query.filter_by(user_id=user_id).count(),
        'research_runs_this_month': user.research_runs_this_month,
        'avg_runtime': db.session.query(func.avg(ResearchRun.runtime_seconds)).filter_by(user_id=user_id).scalar() or 0,
        'total_api_cost': db.session.query(func.sum(ResearchRun.api_cost)).filter_by(user_id=user_id).scalar() or 0,
        'title_performances': TitlePerformance.query.filter_by(user_id=user_id).count(),
        'recent_activity': UserActivity.query.filter_by(user_id=user_id).order_by(UserActivity.created_at.desc()).limit(10).all(),
        'recent_research': ResearchRun.query.filter_by(user_id=user_id).order_by(ResearchRun.created_at.desc()).limit(5).all(),
    }
    
    return stats


def export_users_csv():
    """Export all users to CSV format"""
    from models import User
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'ID', 'Email', 'Username', 'Full Name', 'Niche',
        'Subscription Tier', 'Status', 'Is Admin', 'Is Active',
        'Research Runs This Month', 'Total Research Runs',
        'Created At', 'Last Login'
    ])
    
    # Data
    users = User.query.all()
    for user in users:
        writer.writerow([
            user.id,
            user.email,
            user.username,
            user.full_name or '',
            user.niche or '',
            user.subscription_tier,
            user.subscription_status,
            'Yes' if user.is_admin else 'No',
            'Yes' if user.is_active else 'No',
            user.research_runs_this_month,
            user.total_research_runs,
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
        ])
    
    return output.getvalue()


def export_research_runs_csv():
    """Export all research runs to CSV format"""
    from models import ResearchRun
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'ID', 'User ID', 'Keywords', 'Topics Generated',
        'Sources Successful', 'Runtime (seconds)', 'API Cost',
        'Created At'
    ])
    
    # Data
    runs = ResearchRun.query.order_by(ResearchRun.created_at.desc()).all()
    for run in runs:
        writer.writerow([
            run.id,
            run.user_id,
            ', '.join(run.keywords) if run.keywords else '',
            run.topics_generated,
            run.sources_successful,
            round(run.runtime_seconds, 2) if run.runtime_seconds else 0,
            round(run.api_cost, 4) if run.api_cost else 0,
            run.created_at.strftime('%Y-%m-%d %H:%M:%S') if run.created_at else ''
        ])
    
    return output.getvalue()


# Import timedelta for date calculations
from datetime import timedelta


def send_system_email(recipient_email, subject, template, user_id=None, **kwargs):
    """
    Send a system email and log it to the database
    """
    from models import EmailLog
    
    try:
        # Check if mail extension is initialized
        if 'mail' not in current_app.extensions:
            print("Error: Flask-Mail not initialized.")
            return False

        mail = current_app.extensions['mail']
        
        # Render HTML content
        html_content = render_template(f"emails/{template}.html", **kwargs)
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            html=html_content
        )
        
        # Debug logging
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        print(f"Sending email to {recipient_email}. Subject: {subject}. Sender: {sender}")
        
        # Send email
        mail.send(msg)
        
        # Log success
        log = EmailLog(
            recipient_email=recipient_email,
            user_id=user_id,
            subject=subject,
            template=template,
            status='sent'
        )
        db.session.add(log)
        db.session.commit()
        
        return True
        
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        
        # Log failure
        try:
            log = EmailLog(
                recipient_email=recipient_email,
                user_id=user_id,
                subject=subject,
                template=template,
                status='failed',
                error_message=str(e)
            )
            db.session.add(log)
            db.session.commit()
        except:
            db.session.rollback()
            
        return False
