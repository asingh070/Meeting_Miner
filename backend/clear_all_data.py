"""Script to clear all meetings from database and vector store."""
import sys
import os
import sqlite3
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_session, engine
from backend.models import Meeting, ExtractedData, Project, ChatHistory, Base
from backend.logger import logger

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: chromadb not available. Will only clear database.")


def clear_all_meetings():
    """Delete all meetings from database and vector store."""
    db = get_db_session()
    
    try:
        # Get all meeting IDs before deletion
        meetings = db.query(Meeting).all()
        meeting_ids = [m.id for m in meetings]
        
        logger.info(f"Found {len(meeting_ids)} meetings to delete")
        print(f"Found {len(meeting_ids)} meetings to delete")
        
        if len(meeting_ids) == 0:
            print("No meetings found in database.")
            return
        
        # Delete from vector store (ChromaDB)
        if CHROMADB_AVAILABLE:
            try:
                db_path = os.path.join("data", "chroma_db")
                if os.path.exists(db_path):
                    # Initialize ChromaDB client
                    client = chromadb.PersistentClient(
                        path=db_path,
                        settings=Settings(anonymized_telemetry=False)
                    )
                    
                    # Get the collection
                    try:
                        collection = client.get_collection(name="meeting_transcripts")
                        
                        # Get all IDs and delete them
                        all_results = collection.get()
                        if all_results["ids"]:
                            collection.delete(ids=all_results["ids"])
                            logger.info(f"Cleared {len(all_results['ids'])} chunks from vector store")
                            print(f"✅ Cleared {len(all_results['ids'])} chunks from vector store")
                        else:
                            print("✅ Vector store is already empty")
                    except Exception as e:
                        # Collection might not exist
                        logger.info(f"Collection not found or already empty: {e}")
                        print("✅ Vector store is already empty")
            except Exception as e:
                logger.warning(f"Error clearing vector store: {e}")
                print(f"Warning: Could not clear vector store: {e}")
        else:
            # If chromadb is not available, try to delete the directory
            db_path = os.path.join("data", "chroma_db")
            if os.path.exists(db_path):
                try:
                    shutil.rmtree(db_path)
                    logger.info("Deleted ChromaDB directory")
                    print("✅ Deleted ChromaDB directory")
                except Exception as e:
                    logger.warning(f"Could not delete ChromaDB directory: {e}")
                    print(f"Warning: Could not delete ChromaDB directory: {e}")
        
        # Delete all meetings (cascade will handle related data)
        deleted_count = db.query(Meeting).delete()
        db.commit()
        
        logger.info(f"Deleted {deleted_count} meetings from database")
        print(f"✅ Successfully deleted {deleted_count} meetings from database")
        print("✅ Related data (extracted_data, projects, chat_history) has been automatically deleted due to cascade")
        
    except Exception as e:
        db.rollback()
        error_msg = f"Error clearing meetings: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    # Check if --force flag is provided to skip confirmation
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if not force:
        print("⚠️  WARNING: This will delete ALL meetings and related data!")
        print("This action cannot be undone.")
        response = input("Are you sure you want to continue? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
    
    clear_all_meetings()

