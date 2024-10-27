from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import whisper
import numpy as np
import torch
import asyncio
from typing import List, Dict
import io
import wave
import base64

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Whisper model
model = whisper.load_model("base")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_buffers: Dict[str, List[bytes]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.audio_buffers[client_id] = []
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.audio_buffers:
            del self.audio_buffers[client_id]
            
    async def process_audio(self, client_id: str):
        if not self.audio_buffers.get(client_id):
            return
            
        # Combine audio chunks
        audio_data = b''.join(self.audio_buffers[client_id])
        
        # Convert to wav format
        with io.BytesIO() as wav_io:
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
            
            # Transcribe using Whisper
            result = model.transcribe(wav_io.getvalue(), language='en')
            
            # Send transcription back to client
            if client_id in self.active_connections:
                await self.active_connections[client_id].send_json({
                    "type": "transcript",
                    "text": result["text"]
                })
        
        # Clear buffer after processing
        self.audio_buffers[client_id] = []

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            # Add audio chunk to buffer
            manager.audio_buffers[client_id].append(data)
            
            # Process audio when buffer reaches certain size
            if len(manager.audio_buffers[client_id]) >= 5:  # Process every 5 chunks
                await manager.process_audio(client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}