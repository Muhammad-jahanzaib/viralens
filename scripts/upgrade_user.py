
from app import app, db
from models import User

def upgrade_user():
    with app.app_context():
        # Find the user (assuming single user or first user for now)
        user = User.query.first()
        if user:
            print(f"Found user: {user.username} (Tier: {user.subscription_tier})")
            print(f"Current usage: {user.research_runs_this_month}/{user.total_research_runs}")
            
            # Upgrade to Pro
            user.subscription_tier = 'pro'
            user.research_runs_this_month = 0  # Reset counter too just in case
            
            db.session.commit()
            print(f"✅ User {user.username} upgraded to PRO (Unlimited runs)")
        else:
            print("❌ No user found!")

if __name__ == "__main__":
    upgrade_user()
