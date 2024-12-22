import asyncio
import logging
import json
from typing import Dict, Optional, Callable, Any
from google.cloud import speech
import queue
import threading
import numpy as np
import time
from datetime import datetime
from .stream_manager import StreamManager

logger = logging.getLogger(__name__)

class EnhancedAudioProcessor:
    def __init__(self, websocket: Any, client_id: str, on_transcript: Callable[[dict], None],
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        self.websocket = websocket
        self.client_id = client_id
        self.on_transcript = on_transcript
        self.loop = loop or asyncio.get_event_loop()
        self.current_audio_type = None  # Initialize as None
        self.current_sample_rate = 16000
        self.stream_manager = StreamManager()
        self.audio_queue = queue.Queue()
        self.is_running = True
        self.last_audio_timestamp = time.time()
        self.silence_threshold = 0.01
        self.TIMEOUT_SECONDS = 60
        self.current_chunk_audio_type = None  # Track audio type per chunk
        
        # Initialize Google Speech client with more resilient settings
        self.speech_client = speech.SpeechClient()
        
    async def handle_message(self, message):
        """Handle incoming WebSocket messages with strict audio type tracking"""
        try:
            # If the message is a string, try to parse it as JSON
            if isinstance(message, str):
                data = json.loads(message)
                if data.get('type') == 'audio_meta':
                    # Strictly validate audio type
                    audio_type = data.get('audioType')
                    
                    if audio_type not in ["microphone", "system"]:
                        logger.error(f"Invalid audio type received: {audio_type}")
                        return
                    
                    # Store the audio type for the upcoming chunk
                    self.current_chunk_audio_type = audio_type
                    self.current_audio_type = audio_type  # Update main audio type
                    self.current_sample_rate = data.get('sampleRate', 16000)
                    
                    logger.debug(f"Audio meta received - type: {audio_type}, rate: {self.current_sample_rate}")
                    return
            
            # If we get here, message should be binary audio data
            if isinstance(message, bytes):
                if self.current_chunk_audio_type is None:
                    logger.error("Received audio chunk without preceding metadata")
                    return
                    
                # Use the audio type that was set by the most recent metadata message
                await self.process_chunk(message, self.current_chunk_audio_type)
                
        except json.JSONDecodeError:
            logger.error("Failed to parse message as JSON")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            
    async def process_chunk(self, audio_data: bytes, audio_type: str = "microphone"):
        """Process a new chunk of audio data with strict type checking"""
        try:
            if not self.is_running:
                return False

            if audio_type not in ["microphone", "system"]:
                logger.error(f"Invalid audio type in process_chunk: {audio_type}")
                return False
            
            # Convert bytes to numpy array for audio level check
            data = np.frombuffer(audio_data, dtype=np.int16)
            
            # Check audio level
            max_level = np.max(np.abs(data)) / 32768.0  # Normalize to 0-1
            
            # Only process if audio level is above threshold
            if max_level > self.silence_threshold:
                self.last_audio_timestamp = time.time()
                self.audio_queue.put((audio_type, audio_data))
                
                # Ensure we maintain the audio type through the entire processing chain
                await self.stream_manager.process_audio_chunk(
                    client_id=self.client_id,
                    audio_data=audio_data,
                    audio_type=audio_type  # Pass the specific audio type
                )
                
                logger.debug(f"Processed chunk - type: {audio_type}, level: {max_level}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}", exc_info=True)
            return False

    def _process_audio(self):
        """Main audio processing loop with improved error handling"""
        try:
            logger.info("Starting audio processing loop")
            
            def request_generator():
                while self.is_running:
                    try:
                        # Check for timeout
                        if time.time() - self.last_audio_timestamp > self.TIMEOUT_SECONDS:
                            logger.warning("Audio timeout detected, restarting stream")
                            break

                        try:
                            audio_type, chunk = self.audio_queue.get(timeout=0.1)
                            logger.debug(f"Processing audio chunk of type: {audio_type}")
                        except queue.Empty:
                            continue

                        # Create the streaming request
                        request = speech.StreamingRecognizeRequest(audio_content=chunk)
                        yield request

                    except Exception as e:
                        logger.error(f"Error in request generator: {e}", exc_info=True)
                        if not self.is_running:
                            break
                        time.sleep(0.1)  # Prevent tight loop on error

            streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    model="video",
                    use_enhanced=True,
                    enable_word_time_offsets=True,
                    max_alternatives=1,
                    enable_word_confidence=True,
                    metadata=speech.RecognitionMetadata(
                        interaction_type=speech.RecognitionMetadata.InteractionType.DISCUSSION,
                        microphone_distance=speech.RecognitionMetadata.MicrophoneDistance.NEARFIELD,
                        original_media_type=speech.RecognitionMetadata.OriginalMediaType.AUDIO
                    ),
                ),
                interim_results=True,
                single_utterance=False
            )

            while self.is_running:
                try:
                    logger.info(f"Starting streaming recognition for client: {self.client_id}")
   
                    responses = self.speech_client.streaming_recognize(
                        streaming_config, 
                        request_generator()
                    )
                    
                    for response in responses:
                        if not self.is_running:
                            break

                        if not response.results:
                            continue

                        for result in response.results:
                            if not result.alternatives:
                                continue

                            alternative = result.alternatives[0]
                            transcript = alternative.transcript
                            is_final = result.is_final
                            confidence = alternative.confidence if is_final else None

                            # Create message with current audio type
                            message = {
                                "type": "transcript",
                                "text": transcript,
                                "is_final": is_final,
                                "confidence": confidence,
                                "audioType": self.current_audio_type or "unknown", # Use tracked audio type
                                "timestamp": datetime.now().isoformat()
                            }
                            logger.info(f"Generated transcript for client {self.client_id}: {transcript[:50]}...")
                            # Send through WebSocket
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    self.send_websocket_message(message),
                                    self.loop
                              )
                                future.result(timeout=1)
                                logger.debug("Sent transcript through WebSocket")
                            except Exception as ws_error:
                                logger.error(f"WebSocket send error: {ws_error}")

                            if is_final:
                                try:
                                    logger.info(f"Calling on_transcript for final transcript: {transcript[:50]}...")
                                    future = asyncio.run_coroutine_threadsafe(
                                       self.on_transcript(message),
                                       self.loop
                                )
                                    future.result(timeout=1)
                                    logger.debug("Successfully processed final transcript")
                                except Exception as callback_error:
                                    logger.error(f"Callback error: {callback_error}")    

                      
                except Exception as e:
                    logger.error(f"Error in speech API communication for client {self.client_id}: {e}", exc_info=True)
                    if self.is_running:
                        time.sleep(1)  # Wait before retrying
                        continue
                    break

        except Exception as e:
            logger.error(f"Fatal error in audio processing: {e}", exc_info=True)
        finally:
            logger.info("Audio processing loop ended")

    async def send_websocket_message(self, message: dict):
        """Send message with audio type verification"""
        try:
            if not self.is_running:
                logger.warning("Attempted to send message but processor is not running")
                return

            if self.websocket is None:
                logger.warning("Attempted to send message but websocket is None")
                return

            # Verify audio type for transcript messages
            if message.get('type') == 'transcript':
                audio_type = message.get('audioType')
                if audio_type not in ["microphone", "system", "unknown"]:
                    logger.error(f"Invalid audio type in transcript: {audio_type}")
                    return

            await self.websocket.send_json(message)
            logger.debug(f"Sent message - type: {message.get('type')}, audio type: {message.get('audioType')}")
            
        except Exception as e:
            logger.error(f"Error sending websocket message: {e}", exc_info=True)

    async def start(self):
        """Start the audio processing pipeline"""
        try:
            # Initialize streams
            await self.stream_manager.add_stream(f"{self.client_id}", "microphone")
            await self.stream_manager.add_stream(f"{self.client_id}", "system")
            
            # Start audio processing thread
            self.processing_thread = threading.Thread(target=self._process_audio)
            self.processing_thread.start()
            
            logger.info(f"Started enhanced audio processor for client: {self.client_id}")
            return True
        except Exception as e:
            logger.error(f"Error starting audio processor: {e}")
            return False

    async def stop(self):
        """Stop the audio processor"""
        try:
            self.is_running = False
            if hasattr(self, 'processing_thread'):
                self.processing_thread.join()
            
            # Clean up streams
            await self.stream_manager.remove_stream(self.client_id, "microphone")
            await self.stream_manager.remove_stream(self.client_id, "system")
            
            logger.info(f"Stopped audio processor for client: {self.client_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping audio processor: {e}")
            return False

    def get_status(self) -> dict:
        """Get current status of the processor"""
        return {
            "client_id": self.client_id,
            "is_running": self.is_running,
            "current_audio_type": self.current_audio_type,
            "sample_rate": self.current_sample_rate,
            "streams": self.stream_manager.get_all_stream_statuses()
        }