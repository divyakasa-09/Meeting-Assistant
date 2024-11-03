import sys
import os
from datetime import datetime
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine
from app.database.models import Meeting, Base
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check database connection and tables"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create a session
        db = SessionLocal()
        
        # Check if we can query meetings
        meetings = db.query(Meeting).all()
        logger.info(f"Found {len(meetings)} existing meetings")
        
        # Create a test meeting if none exist
        if len(meetings) == 0:
            test_meeting = Meeting(
                meeting_id=str(uuid.uuid4()),
                title="Test Meeting",
                start_time=datetime.utcnow(),
                is_active=True
            )
            db.add(test_meeting)
            db.commit()
            logger.info("Created test meeting")
        
        # Query again to verify
        meetings = db.query(Meeting).all()
        for meeting in meetings:
            logger.info(f"Meeting ID: {meeting.id}, Title: {meeting.title}, Active: {meeting.is_active}")
        
        db.close()
        logger.info("Database check completed successfully")
        
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        raise

if __name__ == "__main__":
    check_database()