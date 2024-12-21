from typing import Dict, Optional
import numpy as np
import asyncio
import logging
from datetime import datetime
from .buffer import AudioBuffer
from .quality import AudioQualityController

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.audio_buffer = AudioBuffer()
        self.quality_controller = AudioQualityController()
        self.active_streams: Dict[str, dict] = {}
        self.stream_metrics: Dict[str, dict] = {}
        self.last_processed: Dict[str, datetime] = {}

    async def process_audio_chunk(self, client_id: str, audio_data: bytes, audio_type: str = "microphone") -> Optional[dict]:
        """Process a new chunk of audio data"""
        try:
            logger.debug(f"Processing {audio_type} audio chunk for client {client_id}")
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Ensure array is properly shaped for buffer (2D array with shape [samples, 1])
            if audio_array.ndim == 1:
                audio_array = audio_array.reshape(-1, 1)
            
            # Create final stream ID
            final_stream_id = f"{client_id}_{audio_type}"
            
            logger.debug(f"Shaped audio array: {audio_array.shape} for stream {final_stream_id}")
            
            # Add to buffer
            self.audio_buffer.add_audio(final_stream_id, audio_array)
            
            # Update metrics
            self.stream_metrics[final_stream_id] = {
                'last_updated': datetime.now(),
                'chunk_size': len(audio_array),
                'max_amplitude': float(np.max(np.abs(audio_array)))
            }
            
            return {
                'stream_id': final_stream_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': self.stream_metrics[final_stream_id]
            }
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}", exc_info=True)
            return None

    async def add_stream(self, stream_id: str, stream_type: str):
        """
        Add a new audio stream
        stream_type can be 'system' or 'microphone'
        """
        try:
            # Create a unique stream ID based on stream type
            final_stream_id = f"{stream_id}_{stream_type}"

            # Register the stream in active streams
            self.active_streams[final_stream_id] = {
                'type': stream_type,
                'created_at': datetime.now(),
                'is_active': True
            }

            # Add the stream to the audio buffer
            self.audio_buffer.add_stream(final_stream_id)
            logger.info(f"Added new {stream_type} stream: {final_stream_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding stream {stream_id} ({stream_type}): {e}")
            return False

    # async def process_audio_chunk(self, client_id: str, audio_data: bytes) -> Optional[dict]:
    #     try:
    #     # Convert bytes to numpy array directly
    #         audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
    #     # Reshape array to 1D if needed
    #         if audio_array.ndim > 1:
    #            audio_array = audio_array.flatten()
        
    #     # Create final stream ID (assuming microphone for now)
    #         final_stream_id = f"{client_id}_microphone"
        
    #     # Add to buffer directly
    #         self.audio_buffer.add_audio(final_stream_id, audio_array)
        
    #     # Update metrics
    #         self.stream_metrics[final_stream_id] = {
    #         'last_updated': datetime.now(),
    #         }
        
    #         return {
    #         'stream_id': final_stream_id,
    #         'timestamp': datetime.now().isoformat()
    #         }
        
    #     except Exception as e:
    #        logger.error(f"Error processing audio chunk: {e}")
    #        return None
    
    async def get_combined_audio(self) -> Optional[np.ndarray]:
        """Get combined audio from all active streams"""
        try:
            return self.audio_buffer.get_combined_audio()
        except Exception as e:
            logger.error(f"Error getting combined audio: {e}")
            return None

    async def remove_stream(self, stream_id: str, stream_type: str):
        """Remove a stream and clean up its resources"""
        try:
            final_stream_id = f"{stream_id}_{stream_type}"
            if final_stream_id in self.active_streams:
                self.active_streams[final_stream_id]['is_active'] = False
                self.audio_buffer.remove_stream(final_stream_id)
                if final_stream_id in self.stream_metrics:
                    del self.stream_metrics[final_stream_id]
                logger.info(f"Removed stream: {final_stream_id}")
        except Exception as e:
            logger.error(f"Error removing stream {stream_id} ({stream_type}): {e}")

    def get_stream_status(self, stream_id: str, stream_type: str) -> Optional[dict]:
        """Get current status of a stream"""
        final_stream_id = f"{stream_id}_{stream_type}"
        if final_stream_id not in self.active_streams:
            return None

        return {
            **self.active_streams[final_stream_id],
            'metrics': self.stream_metrics.get(final_stream_id, {}),
            'buffer_status': self.audio_buffer.get_buffer_status().get(final_stream_id, {})
        }

    def get_all_stream_statuses(self) -> Dict[str, dict]:
        """Get status of all streams"""
        return {
            stream_id: self.get_stream_status(*stream_id.split('_'))
            for stream_id in self.active_streams.keys()
        }
