import sys
import os
from datetime import datetime, timezone
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine
from app.database.models import Base, Meeting
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    """Update database schema and fix any data issues"""
    try:
        # Create/Update tables
        Base.metadata.create_all(bind=engine)
        
        # Create a session
        db = SessionLocal()
        
        try:
            # Fix any null is_active values
            null_active_meetings = db.query(Meeting).filter(Meeting.is_active.is_(None)).all()
            for meeting in null_active_meetings:
                meeting.is_active = True
                logger.info(f"Fixed is_active for meeting {meeting.id}")
            
            # Fix any null start_time values
            null_start_meetings = db.query(Meeting).filter(Meeting.start_time.is_(None)).all()
            for meeting in null_start_meetings:
                meeting.start_time = datetime.now(timezone.utc)
                logger.info(f"Fixed start_time for meeting {meeting.id}")
            
            # Fix any null meeting_id values
            null_id_meetings = db.query(Meeting).filter(Meeting.meeting_id.is_(None)).all()
            for meeting in null_id_meetings:
                meeting.meeting_id = str(uuid.uuid4())
                logger.info(f"Fixed meeting_id for meeting {meeting.id}")
            
            db.commit()
            logger.info("Database update completed successfully")
            
            # Verify the data
            meetings = db.query(Meeting).all()
            for meeting in meetings:
                logger.info(f"Meeting ID: {meeting.id}, "
                          f"Title: {meeting.title}, "
                          f"Active: {meeting.is_active}, "
                          f"Start: {meeting.start_time}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        raise

if __name__ == "__main__":
    update_database()