
import sqlite3

def update_schema():
    print("Updating database schema...")
    conn = sqlite3.connect('instance/viralens.db')
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(user_configs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'niche_description' not in columns:
        print("Adding niche_description column...")
        cursor.execute("ALTER TABLE user_configs ADD COLUMN niche_description TEXT")
    else:
        print("niche_description already exists.")
        
    if 'research_depth' not in columns:
        print("Adding research_depth column...")
        cursor.execute("ALTER TABLE user_configs ADD COLUMN research_depth TEXT DEFAULT 'standard'")
    else:
        print("research_depth already exists.")
        
    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    update_schema()
