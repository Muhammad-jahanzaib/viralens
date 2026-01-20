import sqlite3
import shutil
import os
import datetime
import sys

# Configuration
DB_PATH = 'instance/viralens.db'
BACKUP_DIR = 'instance/backups'
LOG_FILE = 'migration_log.txt'

def log(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message)
    with open(LOG_FILE, 'a') as f:
        f.write(formatted_message + '\n')

def backup_database():
    if not os.path.exists(DB_PATH):
        log(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)
    
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"viralens.db.backup_{timestamp}")
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        log(f"Database backed up to {backup_path}")
        return backup_path
    except Exception as e:
        log(f"Backup failed: {str(e)}")
        sys.exit(1)

def restore_database(backup_path):
    log("Initiating rollback...")
    try:
        shutil.copy2(backup_path, DB_PATH)
        log("Database restored successfully.")
    except Exception as e:
        log(f"CRITICAL: Restore failed. Manual intervention required. Backup at {backup_path}")

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in cursor.fetchall()]
    return column in columns

def migrate():
    backup_path = backup_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        log("Starting migration...")
        
        # 1. Add columns to users table
        log("Checking 'users' table columns...")
        
        columns_to_add = [
            ('approval_status', "TEXT NOT NULL DEFAULT 'approved'"),
            ('approved_by', "INTEGER REFERENCES users(id)"),
            ('approved_at', "DATETIME"),
            ('rejection_reason', "TEXT"),
            ('admin_notes', "TEXT")
        ]
        
        cols_added = 0
        for col_name, col_def in columns_to_add:
            if not column_exists(cursor, 'users', col_name):
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                    log(f"Added column: {col_name}")
                    cols_added += 1
                except sqlite3.OperationalError as e:
                    # SQLite < 3.35 limitations or other issues
                    log(f"Error adding column {col_name}: {e}")
                    raise e
            else:
                log(f"Column {col_name} already exists. Skipping.")
        
        # 2. Update existing users to 'approved' if needed (handled by DEFAULT, but good to ensure)
        if cols_added > 0:
            cursor.execute("UPDATE users SET approval_status = 'approved' WHERE approval_status IS NULL")
            log("Updated existing users to default approval status.")

        # 3. Create Tables if not exist
        
        # AdminLog
        log("Creating table 'admin_logs' if not exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL REFERENCES users(id),
                action VARCHAR(50) NOT NULL,
                target_type VARCHAR(50),
                target_id INTEGER,
                description TEXT,
                ip_address VARCHAR(50),
                user_agent VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # SystemSettings
        log("Creating table 'system_settings' if not exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) NOT NULL UNIQUE,
                value TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)
        # Index for SystemSettings key
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_system_settings_key ON system_settings(key)")

        # UserActivity
        log("Creating table 'user_activity' if not exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                action VARCHAR(50) NOT NULL,
                details JSON,
                ip_address VARCHAR(50),
                user_agent VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_created_at ON user_activity(created_at)")

        conn.commit()
        log("Migration completed successfully.")
        
    except Exception as e:
        log(f"Migration failed: {str(e)}")
        conn.rollback()
        conn.close()
        restore_database(backup_path)
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print(f"Running migration on {DB_PATH}...")
    migrate()
