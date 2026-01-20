from app import app, db
from models import SystemSettings

def enable_approval():
    with app.app_context():
        setting = SystemSettings.query.filter_by(key='require_approval').first()
        if setting:
            setting.value = 'true'
            print("Updated existing setting: require_approval = true")
        else:
            setting = SystemSettings(key='require_approval', value='true')
            db.session.add(setting)
            print("Created new setting: require_approval = true")
        
        db.session.commit()
        print("✅ Admin approval flow enabled successfully!")

if __name__ == "__main__":
    enable_approval()
