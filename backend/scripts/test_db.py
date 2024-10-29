import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import crud, models, schemas
from app.database.config import SessionLocal

def test_db():
    db = SessionLocal()
    try:
        # Get all meetings
        meetings = db.query(models.Meeting).all()
        print("Existing meetings:")
        for meeting in meetings:
            print(f"- {meeting.meeting_id}: {meeting.title}")
            
            # Get transcripts for each meeting
            transcripts = db.query(models.TranscriptSegment)\
                           .filter(models.TranscriptSegment.meeting_id == meeting.id)\
                           .all()
            print(f"  Transcripts: {len(transcripts)}")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_db()