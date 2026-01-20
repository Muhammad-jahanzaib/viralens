from app import app, db
from models import EmailLog

with app.app_context():
    # Only create the missing table
    db.create_all()
    print("✅ Database tables verified/created (including email_logs).")
