from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine
from app.database.models import Meeting, TranscriptSegment, ActionItem, Summary, FollowUpQuestion
from app.core.meeting_manager import MeetingManager

def test_database_connection():
    """Test basic database connectivity"""
    try:
        # Try to create a session
        db = SessionLocal()
        # Try a simple query with proper text() wrapper
        db.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        return db
    except Exception as e:
        print("❌ Database connection failed!")
        print(f"Error: {str(e)}")
        return None

def test_create_meeting(db: Session):
    """Test creating a meeting"""
    try:
        # Create a test meeting
        meeting = Meeting(
            meeting_id="test-meeting-1",
            title="Test Meeting",
            start_time=datetime.utcnow(),
            is_active=True
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        print("✅ Successfully created test meeting!")
        return meeting
    except Exception as e:
        print("❌ Failed to create meeting!")
        print(f"Error: {str(e)}")
        db.rollback()
        return None

def test_create_transcript(db: Session, meeting_id: int):
    """Test creating a transcript segment"""
    try:
        transcript = TranscriptSegment(
            meeting_id=meeting_id,
            text="This is a test transcript",
            timestamp=datetime.utcnow(),
            speaker="Test Speaker",
            confidence=0.95
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        print("✅ Successfully created test transcript!")
        return transcript
    except Exception as e:
        print("❌ Failed to create transcript!")
        print(f"Error: {str(e)}")
        db.rollback()
        return None

def test_create_action_item(db: Session, meeting_id: int):
    """Test creating an action item"""
    try:
        action_item = ActionItem(
            meeting_id=meeting_id,
            description="Test action item",
            assigned_to="Test User",
            due_date=datetime.utcnow(),
            status="pending"
        )
        db.add(action_item)
        db.commit()
        db.refresh(action_item)
        print("✅ Successfully created test action item!")
        return action_item
    except Exception as e:
        print("❌ Failed to create action item!")
        print(f"Error: {str(e)}")
        db.rollback()
        return None

def test_query_meeting(db: Session, meeting_id: int):
    """Test querying a meeting with all its relationships"""
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            print("\n📊 Meeting Query Results:")
            print(f"Meeting ID: {meeting.id}")
            print(f"Title: {meeting.title}")
            print(f"Start Time: {meeting.start_time}")
            print(f"Is Active: {meeting.is_active}")
            
            print("\nTranscripts:")
            for transcript in meeting.transcripts:
                print(f"- {transcript.text} (Speaker: {transcript.speaker})")
            
            print("\nAction Items:")
            for item in meeting.action_items:
                print(f"- {item.description} (Assigned to: {item.assigned_to})")
            
            print("✅ Successfully queried meeting data!")
            return meeting
        else:
            print("❌ Meeting not found!")
            return None
    except Exception as e:
        print("❌ Failed to query meeting!")
        print(f"Error: {str(e)}")
        return None

def cleanup_test_data(db: Session, meeting_id: int):
    """Clean up test data"""
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            db.delete(meeting)
            db.commit()
            print("✅ Successfully cleaned up test data!")
    except Exception as e:
        print("❌ Failed to clean up test data!")
        print(f"Error: {str(e)}")
        db.rollback()

def run_all_tests():
    print("\n🏃 Running database tests...\n")
    
    # Test database connection
    db = test_database_connection()
    if not db:
        print("❌ Stopping tests due to connection failure!")
        return
    
    try:
        # Create and test a meeting
        meeting = test_create_meeting(db)
        if meeting:
            # Test creating related data
            test_create_transcript(db, meeting.id)
            test_create_action_item(db, meeting.id)
            
            # Query and display all data
            test_query_meeting(db, meeting.id)
            
            # Clean up test data
            cleanup_test_data(db, meeting.id)
    finally:
        db.close()

if __name__ == "__main__":
    run_all_tests()