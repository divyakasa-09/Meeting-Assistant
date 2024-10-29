from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import speech
import asyncio
import logging
import queue
import threading
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

# Import models and database session
from .models import Meeting, Summary, TranscriptSegment, ActionItem, FollowUpQuestion
from .database import SessionLocal, engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AudioProcessor:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.audio_queue = queue.Queue()
        self.is_running = True
        self.client = speech.SpeechClient()

    async def send_message(self, message: dict):
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def process_audio_in_thread(self):
        try:
            streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    use_enhanced=True,
                ),
                interim_results=True
            )

            def request_generator():
                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=1)
                        yield speech.StreamingRecognizeRequest(audio_content=chunk)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Error in request generator: {e}")
                        break

            responses = self.client.streaming_recognize(streaming_config, request_generator())

            for response in responses:
                if not self.is_running:
                    break

                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript
                is_final = result.is_final

                # Send transcription via event loop
                asyncio.run(self.send_message({
                    "type": "transcript",
                    "text": transcript,
                    "is_final": is_final
                }))

        except Exception as e:
            logger.error(f"Error in audio processing thread: {e}")
            asyncio.run(self.send_message({
                "type": "error",
                "message": str(e)
            }))

    def stop(self):
        self.is_running = False

# Store active processors
active_processors: Dict[str, AudioProcessor] = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    logger.info(f"Client connected: {client_id}")

    processor = AudioProcessor(websocket)
    active_processors[client_id] = processor

    thread = threading.Thread(target=processor.process_audio_in_thread)
    thread.start()

    try:
        await websocket.send_json({
            "type": "status",
            "message": "Connected to transcription service"
        })

        while True:
            try:
                audio_data = await websocket.receive_bytes()
                processor.audio_queue.put(audio_data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error receiving audio: {e}")
                break

    finally:
        if client_id in active_processors:
            active_processors[client_id].stop()
            del active_processors[client_id]
        logger.info(f"Client disconnected: {client_id}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(active_processors)
    }

# New endpoint: Create summary
@app.post("/summaries/")
def create_summary(meeting_id: int, summary_text: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    summary = Summary(meeting_id=meeting_id, summary_text=summary_text)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary

# New endpoint: Create action item
@app.post("/action-items/")
def create_action_item(meeting_id: int, description: str, assigned_to: str, db: Session = Depends(get_db)):
    action_item = ActionItem(meeting_id=meeting_id, description=description, assigned_to=assigned_to)
    db.add(action_item)
    db.commit()
    db.refresh(action_item)
    return action_item

# New endpoint: Add follow-up question
@app.post("/follow-up-questions/")
def add_follow_up_question(meeting_id: int, question_text: str, db: Session = Depends(get_db)):
    question = FollowUpQuestion(meeting_id=meeting_id, question_text=question_text)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question
