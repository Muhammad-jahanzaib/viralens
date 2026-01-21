
import os
import sys

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, SystemSettings

def enable_approval():
    # Initialize minimal app
    app = Flask(__name__)
    
    # Database Configuration
    # Prioritize DATABASE_URL from environment (for Production/Railway)
    uri = os.environ.get('DATABASE_URL')
    if uri:
        if uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        print(f"🔌  Using environment database: {uri.split('@')[1] if '@' in uri else '...redacted...'}")
    else:
        # Fallback to local SQLite (Instance folder)
        db_path = os.path.join(os.getcwd(), 'instance', 'viralens.db')
        uri = f'sqlite:///{db_path}'
        print(f"🔌  Using local database: {db_path}")

    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize DB with this app
    db.init_app(app)
    
    with app.app_context():
        try:
            setting = SystemSettings.query.filter_by(key='require_approval').first()
            if setting:
                setting.value = 'true'
                print(f"✅ Updated existing setting: require_approval = true (previous: {setting.value})")
            else:
                setting = SystemSettings(key='require_approval', value='true')
                db.session.add(setting)
                print("✅ Created new setting: require_approval = true")
            
            db.session.commit()
            print("🎉 Success! Admin approval flow is now ENABLED.")
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            print("Tip: Ensure you are running this from the project root.")

if __name__ == "__main__":
    enable_approval()
