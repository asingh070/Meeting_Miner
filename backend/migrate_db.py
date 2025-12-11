"""Database migration script to add new columns to extracted_data table."""
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.config import Config
    from backend.logger import logger
except ImportError:
    # Fallback if imports fail
    import logging
    logger = logging.getLogger(__name__)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/meetingminer.db")
else:
    DATABASE_URL = Config.DATABASE_URL


def migrate_database():
    """Add new columns to extracted_data table if they don't exist."""
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    
    # Handle absolute paths
    if not os.path.isabs(db_path):
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(script_dir, db_path)
    
    # Create data directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    if not os.path.exists(db_path):
        logger.info(f"Database file {db_path} does not exist. It will be created on first run.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='extracted_data'")
        if not cursor.fetchone():
            logger.info("Table extracted_data does not exist. It will be created on first run.")
            conn.close()
            return
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(extracted_data)")
        columns = [row[1] for row in cursor.fetchall()]
        
        changes_made = False
        
        # Add new columns if they don't exist
        if 'pain_points_json' not in columns:
            logger.info("Adding pain_points_json column...")
            print("Adding pain_points_json column...")
            cursor.execute("ALTER TABLE extracted_data ADD COLUMN pain_points_json TEXT")
            changes_made = True
        
        # Handle ideas_scope_json (new name) - migrate from ideas_proposals_json if exists
        if 'ideas_scope_json' not in columns:
            if 'ideas_proposals_json' in columns:
                logger.info("Migrating ideas_proposals_json to ideas_scope_json...")
                print("Migrating ideas_proposals_json to ideas_scope_json...")
                # Copy data from old column to new column
                cursor.execute("ALTER TABLE extracted_data ADD COLUMN ideas_scope_json TEXT")
                cursor.execute("UPDATE extracted_data SET ideas_scope_json = ideas_proposals_json WHERE ideas_proposals_json IS NOT NULL")
            else:
                logger.info("Adding ideas_scope_json column...")
                print("Adding ideas_scope_json column...")
                cursor.execute("ALTER TABLE extracted_data ADD COLUMN ideas_scope_json TEXT")
            changes_made = True
        
        # Handle project_details_json (new name) - migrate from projects_json if exists
        if 'project_details_json' not in columns:
            if 'projects_json' in columns:
                logger.info("Migrating projects_json to project_details_json...")
                print("Migrating projects_json to project_details_json...")
                # Copy data from old column to new column
                cursor.execute("ALTER TABLE extracted_data ADD COLUMN project_details_json TEXT")
                cursor.execute("UPDATE extracted_data SET project_details_json = projects_json WHERE projects_json IS NOT NULL")
            else:
                logger.info("Adding project_details_json column...")
                print("Adding project_details_json column...")
                cursor.execute("ALTER TABLE extracted_data ADD COLUMN project_details_json TEXT")
            changes_made = True
        
        if 'overall_sentiment' not in columns:
            logger.info("Adding overall_sentiment column...")
            print("Adding overall_sentiment column...")
            cursor.execute("ALTER TABLE extracted_data ADD COLUMN overall_sentiment VARCHAR(50)")
            changes_made = True
        
        # Check meetings table for project_name column
        cursor.execute("PRAGMA table_info(meetings)")
        meeting_columns = [row[1] for row in cursor.fetchall()]
        
        if 'project_name' not in meeting_columns:
            logger.info("Adding project_name column to meetings table...")
            print("Adding project_name column to meetings table...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN project_name VARCHAR(500)")
            changes_made = True
        
        conn.commit()
        
        if changes_made:
            logger.info("Database migration completed successfully!")
            print("✅ Database migration completed successfully!")
        else:
            logger.info("Database is already up to date.")
            print("✅ Database is already up to date.")
        
    except Exception as e:
        conn.rollback()
        error_msg = f"Error migrating database: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()

