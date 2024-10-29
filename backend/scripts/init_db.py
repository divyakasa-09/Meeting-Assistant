import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import crud, models, schemas
from app.database.config import SessionLocal, engine
from app.database.models import Base

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Initializing test data...")
    db = SessionLocal()
    try:
        # Create a test meeting
        meeting = crud.create_meeting(
            db, 
            schemas.MeetingCreate(
                meeting_id="test-meeting-1",
                title="Test Meeting"
            )
        )
        print(f"Created meeting: {meeting.meeting_id}")

        # Add a test transcript
        segment = crud.add_transcript_segment(
            db, 
            meeting.meeting_id, 
            "Hello, this is a test transcript"
        )
        print("Added test transcript segment")

    finally:
        db.close()

if __name__ == "__main__":
    init_db()