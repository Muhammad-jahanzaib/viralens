import sqlite3
import os

def restore_admin():
    backup_path = 'instance/viralens.db.backup'
    active_path = 'instance/viralens.db'
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        return
    
    try:
        # Connect to databases
        backup_conn = sqlite3.connect(backup_path)
        active_conn = sqlite3.connect(active_path)
        
        backup_cursor = backup_conn.cursor()
        active_cursor = active_conn.cursor()
        
        # Ensure users table exists in active (if not, running create_all might be better but let's assume it exists if app was started)
        # To be safe, let's just copy the row if possible or use SQLAlchemy if we want to be clean.
        # But SQL is faster for a simple row copy.
        
        # Get admin row data from backup
        # Note: We need to match the columns of the active DB.
        # Active DB columns (from models.py): id, email, username, password_hash, full_name, niche, subscription_tier, 
        # subscription_status, subscription_start, subscription_end, research_runs_this_month, total_research_runs, 
        # is_admin, is_active, created_at, last_login, approval_status, approved_by, approved_at, rejection_reason, 
        # admin_notes, onboarding_completed, onboarding_step
        
        backup_cursor.execute("SELECT * FROM users WHERE is_admin = 1;")
        admin_row = backup_cursor.fetchone()
        
        if not admin_row:
            print("⚠️ No admin found in backup.")
            return
            
        # Get column names from backup
        backup_columns = [description[0] for description in backup_cursor.description]
        
        # Get column names from active
        active_cursor.execute("PRAGMA table_info(users);")
        active_columns = [row[1] for row in active_cursor.fetchall()]
        
        print(f"Backup columns: {len(backup_columns)}")
        print(f"Active columns: {len(active_columns)}")
        
        # Create a mapping for insertion
        placeholders = []
        values = []
        insert_cols = []
        
        admin_dict = dict(zip(backup_columns, admin_row))
        
        for col in active_columns:
            if col in admin_dict:
                insert_cols.append(col)
                placeholders.append("?")
                values.append(admin_dict[col])
            else:
                # Provide defaults for new columns if necessary
                if col == 'approval_status':
                    insert_cols.append(col)
                    placeholders.append("?")
                    values.append('approved')
                elif col == 'onboarding_completed':
                    insert_cols.append(col)
                    placeholders.append("?")
                    values.append(1)
                elif col == 'onboarding_step':
                    insert_cols.append(col)
                    placeholders.append("?")
                    values.append(4) # Assuming final step
        
        # Check if admin already exists in active
        active_cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (admin_dict['username'], admin_dict['email']))
        if active_cursor.fetchone():
            print(f"ℹ️ Admin {admin_dict['username']} already exists in active DB. Updating...")
            # Update logic could be added here, but for now let's just delete and re-insert for a clean restore
            active_cursor.execute("DELETE FROM users WHERE username = ? OR email = ?", (admin_dict['username'], admin_dict['email']))

        sql = f"INSERT INTO users ({', '.join(insert_cols)}) VALUES ({', '.join(placeholders)})"
        active_cursor.execute(sql, tuple(values))
        
        active_conn.commit()
        print(f"✅ Admin account '{admin_dict['username']}' restored to active database.")
        
        backup_conn.close()
        active_conn.close()
        
    except Exception as e:
        print(f"❌ Error during restore: {e}")

if __name__ == "__main__":
    restore_admin()
