from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload 

from datetime import datetime, timezone
import logging
import json
import asyncio
import threading
from typing import Dict, Optional, List
import uuid
from .services.ai_service import AIService
from fastapi import BackgroundTasks
from .database.models import Meeting, Summary, TranscriptSegment, ActionItem
from .database import schemas
from .database.config import SessionLocal, engine
from .core.audio.processor import EnhancedAudioProcessor
from .services.enhanced_ai_service import EnhancedAIService 
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
ai_service = EnhancedAIService()
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Store active processors
active_processors: Dict[str, EnhancedAudioProcessor] = {}

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def handle_transcript(meeting_id: str, transcript_data: dict, db: Session):
    """Handle incoming transcript data"""
    try:
        logger.info(f"START handle_transcript for meeting {meeting_id}")
        logger.info(f"Transcript data: {transcript_data}")
        
        if transcript_data.get("is_final"):
            logger.info(f"Processing final transcript for meeting {meeting_id}")
            
            # Get the meeting first
            meeting = db.query(Meeting)\
                .filter(Meeting.meeting_id == meeting_id)\
                .first()
                
            if not meeting:
                logger.error(f"Meeting {meeting_id} not found when saving transcript")
                return

            logger.info(f"Found meeting with ID {meeting.id} for transcript")

            # Create transcript
            transcript = TranscriptSegment(
                meeting_id=meeting.id,
                text=transcript_data["text"],
                timestamp=datetime.now(timezone.utc),
                confidence=transcript_data.get("confidence"),
                speaker=transcript_data.get("speaker"),
                audio_type=transcript_data.get("audioType", "microphone")
            )
            
            logger.info(f"Created transcript object: {transcript.text[:100]}...")
            logger.info(f"Audio type: {transcript.audio_type}")
            
            try:
                db.add(transcript)
                logger.info("Added transcript to session")
                
                db.commit()
                db.refresh(transcript)
                logger.info(f"Successfully saved transcript with ID {transcript.id}")

                # Verify the transcript was saved
                saved_transcript = db.query(TranscriptSegment)\
                    .filter(TranscriptSegment.id == transcript.id)\
                    .first()
                    
                if saved_transcript:
                    logger.info("Verified transcript was saved correctly")
                else:
                    logger.error("Failed to verify saved transcript")

            except Exception as commit_error:
                logger.error(f"Error committing transcript: {commit_error}")
                logger.exception(commit_error)  # Log full stack trace
                logger.exception(e) 
                db.rollback()
                raise
            
    except Exception as e:
        logger.error(f"Error handling transcript: {e}")
        logger.exception(e)  # Log full stack trace
        db.rollback()
        

def verify_transcript_saved(db: Session, meeting_id: int, text: str) -> bool:
    """Verify if a transcript was saved successfully"""
    try:
        transcript = db.query(TranscriptSegment)\
            .filter(
                TranscriptSegment.meeting_id == meeting_id,
                TranscriptSegment.text == text
            )\
            .first()
        return transcript is not None
    except Exception as e:
        logger.error(f"Error verifying transcript: {e}")
        return False
            

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str, 
    db: Session = Depends(get_db)
):
    try:
        await websocket.accept()
        logger.info(f"Client connected: {client_id}")

        # Get the current event loop
        loop = asyncio.get_running_loop()
        
        # Initialize the enhanced audio processor
        processor = EnhancedAudioProcessor(
            websocket=websocket,
            client_id=client_id,
            on_transcript=lambda x: handle_transcript(client_id, x, db),
            loop=loop
        )
        
        active_processors[client_id] = processor
        
        # Start the processor
        if not await processor.start():
            logger.error(f"Failed to start audio processor for client: {client_id}")
            await websocket.close(code=1011)
            return

        await websocket.send_json({
            "type": "status",
            "message": "Connected to transcription service",
            "client_id": client_id
        })

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=30.0)
                
                if message["type"] == "websocket.disconnect":
                    logger.info(f"Client initiated disconnect: {client_id}")
                    break
                    
                if "bytes" in message:
                    logger.info(f"Received audio chunk from {client_id} size: {len(message['bytes'])}")
                    await processor.process_chunk(message["bytes"], "microphone")
                elif "text" in message:
                    data = json.loads(message["text"])
                    logger.info(f"Received text message from {client_id}: {data.get('type')}")
                    if data.get("type") == "audio_meta":
                        await processor.handle_message(message["text"])
                    elif data.get("type") == "system_audio":
                        logger.info(f"Processing system audio chunk size: {len(data['audio'])}")
                        await processor.process_chunk(data["audio"], "system")

            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception as e:
                    logger.error(f"Failed to send ping: {e}")
                    break
                continue
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for client: {client_id}")
                break
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.exception(e)  # This will log the full stack trace
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except:
                    break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        logger.exception(e)
        
    finally:
        try:
            if client_id in active_processors:
                await active_processors[client_id].stop()
                del active_processors[client_id]
            logger.info(f"Client disconnected and cleanup completed: {client_id}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            logger.exception(e)


@app.post("/meetings/{meeting_id}/test-transcript")
async def create_test_transcript(meeting_id: str, db: Session = Depends(get_db)):
    try:
        # Find the meeting
        meeting = db.query(Meeting)\
            .filter(Meeting.meeting_id == meeting_id)\
            .first()
            
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        # Create a test transcript
        transcript = TranscriptSegment(
            meeting_id=meeting.id,
            text="This is a test transcript",
            timestamp=datetime.now(timezone.utc),
            speaker="Test Speaker"
        )
        
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        return JSONResponse(
            content={
                "message": "Test transcript created",
                "transcript_id": transcript.id,
                "meeting_id": meeting_id
            }
        )
    except Exception as e:
        logger.error(f"Error creating test transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    db.delete(meeting)
    db.commit()
    return {"message": "Meeting deleted successfully"}
   
@app.get("/debug/active-meetings")
async def get_active_meetings(db: Session = Depends(get_db)):
    try:
        # Get all meetings
        meetings = db.query(Meeting)\
            .order_by(Meeting.start_time.desc())\
            .limit(5)\
            .all()
            
        return JSONResponse(
            content={
                "meetings": [
                    {
                        "id": meeting.id,
                        "meeting_id": meeting.meeting_id,
                        "title": meeting.title,
                        "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                        "is_active": meeting.is_active
                    } for meeting in meetings
                ]
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
    
@app.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "active_connections": len(active_processors),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.post("/meetings/")
async def create_meeting(title: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        meeting = Meeting(
            meeting_id=str(uuid.uuid4()),
            title=title or f"Meeting {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            start_time=datetime.now(timezone.utc),
            is_active=True
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        logger.info(f"Created new meeting: {meeting.id}")
        
        return JSONResponse(
            content={
                "id": meeting.id,
                "meeting_id": meeting.meeting_id,
                "title": meeting.title,
                "start_time": meeting.start_time.isoformat(),
                "end_time": None,
                "is_active": meeting.is_active,
                "transcripts": [],
                "action_items": []
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        logger.error(f"Error creating meeting: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/meetings/")
async def list_meetings(db: Session = Depends(get_db)):
    try:
        # Get all meetings ordered by start time
        meetings = db.query(Meeting)\
            .order_by(Meeting.start_time.desc())\
            .all()

        response_data = []
        
        for meeting in meetings:
            # Get transcripts for this meeting
            transcripts = db.query(TranscriptSegment)\
                .filter(TranscriptSegment.meeting_id == meeting.id)\
                .order_by(TranscriptSegment.timestamp.asc())\
                .all()
                
            # Get action items for this meeting
            action_items = db.query(ActionItem)\
                .filter(ActionItem.meeting_id == meeting.id)\
                .all()

            meeting_data = {
                "id": meeting.id,
                "meeting_id": meeting.meeting_id,
                "title": meeting.title,
                "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
                "is_active": meeting.is_active,
                "transcripts": [
                    {
                        "id": t.id,
                        "text": t.text,
                        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        "speaker": t.speaker,
                        "confidence": t.confidence if hasattr(t, 'confidence') else None
                    } for t in transcripts
                ],
                "action_items": [
                    {
                        "id": a.id,
                        "description": a.description,
                        "status": a.status,
                        "assigned_to": a.assigned_to if hasattr(a, 'assigned_to') else None,
                        "created_at": a.created_at.isoformat() if hasattr(a, 'created_at') and a.created_at else None
                    } for a in action_items
                ]
            }
            response_data.append(meeting_data)

        return JSONResponse(
            content=response_data,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        logger.error(f"Error fetching meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    
@app.get("/debug/meeting/{meeting_id}/transcripts")
async def debug_meeting_transcripts(meeting_id: str, db: Session = Depends(get_db)):
    try:
        # Get the meeting
        meeting = db.query(Meeting)\
            .filter(Meeting.meeting_id == meeting_id)\
            .first()
            
        if not meeting:
            return JSONResponse(
                content={"error": "Meeting not found"},
                status_code=404
            )
            
        # Get transcripts directly
        transcripts = db.query(TranscriptSegment)\
            .filter(TranscriptSegment.meeting_id == meeting.id)\
            .order_by(TranscriptSegment.timestamp.asc())\
            .all()
            
        return JSONResponse(
            content={
                "meeting_id": meeting_id,
                "meeting_db_id": meeting.id,
                "transcript_count": len(transcripts),
                "transcripts": [
                    {
                        "id": t.id,
                        "text": t.text,
                        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        "speaker": t.speaker
                    } for t in transcripts
                ]
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
@app.get("/meetings/{meeting_id}/debug")
async def debug_meeting(meeting_id: str, db: Session = Depends(get_db)):
    try:
        # Get meeting
        meeting = db.query(Meeting)\
            .filter(Meeting.meeting_id == meeting_id)\
            .first()
            
        if not meeting:
            raise HTTPException(status_code=404, detail=f"Meeting not found with ID: {meeting_id}")
            
        # Get transcripts directly
        transcripts = db.query(TranscriptSegment)\
            .filter(TranscriptSegment.meeting_id == meeting.id)\
            .all()
            
        # Get raw data
        return JSONResponse(
            content={
                "meeting": {
                    "id": meeting.id,
                    "meeting_id": meeting.meeting_id,
                    "title": meeting.title,
                    "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                    "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
                    "is_active": meeting.is_active
                },
                "transcripts_count": len(transcripts),
                "transcripts_data": [
                    {
                        "id": t.id,
                        "meeting_id": t.meeting_id,  # This should match meeting.id
                        "text": t.text,
                        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        "speaker": t.speaker
                    } for t in transcripts
                ],
                "database_info": {
                    "meeting_table_name": Meeting.__tablename__,
                    "transcript_table_name": TranscriptSegment.__tablename__,
                    "transcript_foreign_key": str(TranscriptSegment.meeting_id.property.columns[0].foreign_keys)
                }
            }
        )
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/meetings/{meeting_id}/details")
async def get_meeting_details(meeting_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching details for meeting: {meeting_id}")
        
        # Find the meeting first
        meeting = db.query(Meeting)\
            .filter(Meeting.meeting_id == meeting_id)\
            .first()

        if not meeting:
            logger.warning(f"Meeting not found: {meeting_id}")
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Get transcripts with explicit ordering
        transcripts = db.query(TranscriptSegment)\
            .filter(TranscriptSegment.meeting_id == meeting.id)\
            .order_by(TranscriptSegment.timestamp.asc())\
            .all()

        # Get action items
        action_items = db.query(ActionItem)\
            .filter(ActionItem.meeting_id == meeting.id)\
            .order_by(ActionItem.created_at.desc())\
            .all()

        logger.info(f"Found {len(transcripts)} transcripts for meeting {meeting_id}")
        
        # Prepare response data
        response_data = {
            "id": meeting.id,
            "meeting_id": meeting.meeting_id,
            "title": meeting.title,
            "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
            "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
            "is_active": meeting.is_active,
            "transcripts": [
                {
                    "id": t.id,
                    "text": t.text,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                    "speaker": t.speaker,
                    "confidence": t.confidence if hasattr(t, 'confidence') else None
                } for t in transcripts
            ] if transcripts else [],
            "action_items": [
                {
                    "id": a.id,
                    "description": a.description,
                    "status": a.status,
                    "assigned_to": a.assigned_to if hasattr(a, 'assigned_to') else None,
                } for a in action_items
            ] if action_items else []
        }

        # Log the response
        logger.info(f"Returning response with {len(response_data['transcripts'])} transcripts")
        logger.info(f"First transcript: {response_data['transcripts'][0] if response_data['transcripts'] else 'No transcripts'}")
        
        return JSONResponse(
            content=response_data,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/meetings/{meeting_id}/transcripts")
async def get_meeting_transcripts(meeting_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching transcripts for meeting: {meeting_id}")
        
        # Find the meeting
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        # Get transcripts directly
        transcripts = db.query(TranscriptSegment)\
            .filter(TranscriptSegment.meeting_id == meeting.id)\
            .order_by(TranscriptSegment.timestamp.asc())\
            .all()
            
        logger.info(f"Found {len(transcripts)} transcripts for meeting {meeting_id}")
        
        return JSONResponse(
            content={
                "meeting_id": meeting_id,
                "transcripts": [
                    {
                        "id": t.id,
                        "text": t.text,
                        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        "speaker": t.speaker if hasattr(t, 'speaker') else None,
                        "confidence": t.confidence if hasattr(t, 'confidence') else None
                    } for t in transcripts
                ]
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/meetings/{meeting_id}/test-transcripts")
async def create_test_transcripts(meeting_id: str, db: Session = Depends(get_db)):
    try:
        # Find the meeting
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        # Create some test transcripts
        test_texts = [
            "Hello, this is a test transcript.",
            "This is another test transcript.",
            "And one final test transcript."
        ]
        
        created_transcripts = []
        for text in test_texts:
            transcript = TranscriptSegment(
                meeting_id=meeting.id,
                text=text,
                timestamp=datetime.now(timezone.utc),
                speaker="Test Speaker"
            )
            db.add(transcript)
            created_transcripts.append(transcript)
        
        db.commit()
        
        return JSONResponse(
            content={
                "message": "Test transcripts created",
                "count": len(created_transcripts),
                "transcripts": [
                    {
                        "id": t.id,
                        "text": t.text,
                        "timestamp": t.timestamp.isoformat()
                    } for t in created_transcripts
                ]
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test transcripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))    
    
@app.post("/meetings/{meeting_id}/generate-summary")
async def generate_meeting_summary(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    try:
        # Find the meeting
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Get all transcripts for the meeting
        transcripts = db.query(TranscriptSegment)\
            .filter(TranscriptSegment.meeting_id == meeting.id)\
            .order_by(TranscriptSegment.timestamp.asc())\
            .all()

        if not transcripts:
            raise HTTPException(status_code=400, detail="No transcripts found for meeting")

        # Prepare messages for GPT
        messages = [
            {
                "role": "system",
                "content": "You are a meeting assistant. Provide a clear and concise summary of the meeting, highlighting key points, decisions, and action items."
            },
            {
                "role": "user",
                "content": f"Please summarize this meeting transcript: \n\n{' '.join([t.text for t in transcripts])}"
            }
        ]

        # Generate summary using OpenAI
        summary_text = await ai_service.process_with_retry(messages)

        if summary_text:
            # Save summary to database
            summary = Summary(
                meeting_id=meeting.id,
                summary_text=summary_text,
            )
            db.add(summary)
            db.commit()
            db.refresh(summary)

            return JSONResponse(
                content={
                    "status": "success",
                    "meeting_id": meeting_id,
                    "summary": summary_text
                },
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate summary")

    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add endpoint for getting AI service usage stats
@app.get("/ai-usage-stats")
async def get_ai_usage_stats():
    try:
        stats = ai_service.get_usage_stats()
        return JSONResponse(
            content=stats,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        logger.error(f"Error getting AI usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Optionally, add an endpoint for real-time summary updates during the meeting
@app.post("/meetings/{meeting_id}/progressive-summary")
async def generate_progressive_summary(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    try:
        # Get the most recent transcripts (e.g., last 5 minutes)
        meeting = db.query(Meeting)\
            .filter(Meeting.meeting_id == meeting_id)\
            .first()
            
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        recent_transcripts = db.query(TranscriptSegment)\
            .filter(
                TranscriptSegment.meeting_id == meeting.id,
                TranscriptSegment.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=5)
            )\
            .order_by(TranscriptSegment.timestamp.asc())\
            .all()

        if not recent_transcripts:
            return JSONResponse(
                content={
                    "status": "no_update",
                    "message": "No recent transcripts to summarize"
                }
            )

        messages = [
            {
                "role": "system",
                "content": "You are a real-time meeting assistant. Provide a brief summary of the recent discussion points."
            },
            {
                "role": "user",
                "content": f"Summarize the recent discussion: \n\n{' '.join([t.text for t in recent_transcripts])}"
            }
        ]

        summary_text = await ai_service.process_with_retry(messages)
        
        if summary_text:
            return JSONResponse(
                content={
                    "status": "success",
                    "meeting_id": meeting_id,
                    "progressive_summary": summary_text
                },
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )

    except Exception as e:
        logger.error(f"Error generating progressive summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    db.delete(meeting)
    db.commit()
    return {"message": "Meeting deleted successfully"}

@app.put("/meetings/{meeting_id}/end")
async def end_meeting(meeting_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Attempting to end meeting: {meeting_id}")
        
        # Find meeting by meeting_id
        meeting = db.query(Meeting)\
            .filter(Meeting.meeting_id == meeting_id)\
            .first()
            
        if not meeting:
            logger.error(f"Meeting not found: {meeting_id}")
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        logger.info(f"Found meeting {meeting_id}, setting end time and status")
        
        meeting.end_time = datetime.now(timezone.utc)
        meeting.is_active = False
        
        try:
            db.commit()
            logger.info(f"Successfully ended meeting {meeting_id}")
        except Exception as commit_error:
            logger.error(f"Error committing changes: {commit_error}")
            db.rollback()
            raise
        
        return JSONResponse(
            content={
                "message": "Meeting ended successfully",
                "meeting_id": meeting.meeting_id,
                "end_time": meeting.end_time.isoformat(),
                "is_active": meeting.is_active
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending meeting: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/meetings/{meeting_id}/live-insights")
async def generate_live_insights(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Generating insights for meeting {meeting_id}")
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Get recent transcripts
        recent_transcripts = db.query(TranscriptSegment)\
            .filter(TranscriptSegment.meeting_id == meeting.id)\
            .order_by(TranscriptSegment.timestamp.desc())\
            .limit(10)\
            .all()

        transcript_texts = [t.text for t in recent_transcripts]
        
        logger.info(f"Processing {len(transcript_texts)} transcript segments")
        
        # Generate insights using AI service
        summary = await ai_service.generate_progressive_summary(transcript_texts)
        logger.info(f"Generated summary: {summary}")
        
        questions = await ai_service.generate_followup_questions(' '.join(transcript_texts))
        logger.info(f"Generated questions: {questions}")
        
        action_items = await ai_service.extract_action_items(' '.join(transcript_texts))
        logger.info(f"Generated action items: {action_items}")

        return JSONResponse(content={
            "summary": json.loads(summary) if summary else None,
            "questions": json.loads(questions) if questions else None,
            "action_items": json.loads(action_items) if action_items else None
        })

    except Exception as e:
        logger.error(f"Error generating live insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)