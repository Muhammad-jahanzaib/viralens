from app import app, db
from models import User, ResearchRun

def check_user_data():
    with app.app_context():
        users = User.query.all()
        print(f"Total Users: {len(users)}")
        for u in users:
            runs = ResearchRun.query.filter_by(user_id=u.id).count()
            print(f"User: {u.username} (ID: {u.id}) - Runs: {runs}")
            if runs > 0:
                last_run = ResearchRun.query.filter_by(user_id=u.id).order_by(ResearchRun.created_at.desc()).first()
                print(f"  Last Run: {last_run.created_at} - Topics: {last_run.topics_generated}")

if __name__ == "__main__":
    check_user_data()
