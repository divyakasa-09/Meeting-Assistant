import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from google.cloud import speech
import queue
import threading
from datetime import datetime
from .stream_manager import StreamManager

logger = logging.getLogger(__name__)

class EnhancedAudioProcessor:
    def __init__(self, 
                 websocket: Any, 
                 client_id: str, 
                 on_transcript: Callable[[dict], None],
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        self.websocket = websocket
        self.client_id = client_id
        self.on_transcript = on_transcript
        self.loop = loop or asyncio.get_event_loop()
        
        # Initialize components
        self.stream_manager = StreamManager()
        self.audio_queue = queue.Queue()
        self.is_running = True
        
        # Initialize Google Speech client
        self.speech_client = speech.SpeechClient()

    async def start(self):
        """Start the audio processing pipeline"""
        try:
            # Initialize streams with simple IDs
            await self.stream_manager.add_stream(f"{self.client_id}", "microphone")
            logger.info(f"Started enhanced audio processor for client: {self.client_id}")
            return True
        except Exception as e:
            logger.error(f"Error starting audio processor: {e}")
            return False

    async def send_websocket_message(self, message: dict):
        """Helper method to send messages through websocket"""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending websocket message: {e}")

    def _process_audio(self):
        """Main audio processing loop"""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

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

            responses = self.speech_client.streaming_recognize(streaming_config, request_generator())

            for response in responses:
                if not self.is_running:
                    break

                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence if result.is_final else None
                is_final = result.is_final

                # Create message
                message = {
                    "type": "transcript",
                    "text": transcript,
                    "is_final": is_final,
                    "confidence": confidence
                }

                # Schedule the coroutine in the main event loop
                future = asyncio.run_coroutine_threadsafe(
                    self.send_websocket_message(message),
                    self.loop
                )
                future.result()  # Wait for the result

                if is_final:
                    future = asyncio.run_coroutine_threadsafe(
                        self.on_transcript(message),
                        self.loop
                    )
                    future.result()  # Wait for the result

        except Exception as e:
            logger.error(f"Error in audio processing: {e}")
            if self.is_running:
                future = asyncio.run_coroutine_threadsafe(
                    self.send_websocket_message({
                        "type": "error",
                        "message": str(e)
                    }),
                    self.loop
                )
                future.result()
        finally:
            loop.close()

    async def process_chunk(self, audio_data: bytes, stream_type: str = "microphone"):
        """Process a new chunk of audio data"""
        try:
            if stream_type == "microphone":
                self.audio_queue.put(audio_data)
            
            result = await self.stream_manager.process_audio_chunk(self.client_id, audio_data)
            return True
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return False

    async def stop(self):
        """Stop the audio processor"""
        try:
            self.is_running = False
            if hasattr(self, 'processing_thread'):
                self.processing_thread.join()
            
            # Clean up stream
            await self.stream_manager.remove_stream(self.client_id)
            
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
            "streams": self.stream_manager.get_all_stream_statuses()
        }