from typing import Dict, Optional, List
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

    async def add_stream(self, stream_id: str, stream_type: str):
        """
        Add a new audio stream
        stream_type can be 'system' or 'microphone'
        """
        try:
            # Create proper stream ID based on type
            final_stream_id = stream_id
            if stream_type == "microphone":
                final_stream_id = f"{stream_id}_mic"
            elif stream_type == "system":
                final_stream_id = f"{stream_id}_sys"

            self.active_streams[final_stream_id] = {
                'type': stream_type,
                'created_at': datetime.now(),
                'is_active': True
            }
            self.audio_buffer.add_stream(final_stream_id)
            logger.info(f"Added new {stream_type} stream: {final_stream_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding stream {stream_id}: {e}")
            return False

    async def process_audio_chunk(self, stream_id: str, audio_data: bytes) -> Optional[dict]:
        """Process incoming audio chunk and return processing results"""
        try:
            if stream_id not in self.active_streams:
                logger.warning(f"Received audio for unknown stream: {stream_id}")
                return None

            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Process audio quality
            processed_audio, is_speech = self.quality_controller.process_audio(audio_array)
            
            # Get quality metrics
            quality_metrics = self.quality_controller.check_quality(processed_audio)
            
            # Add to buffer if quality is good enough
            if quality_metrics['rms_level'] > 0.01 or is_speech:
                self.audio_buffer.add_audio(stream_id, processed_audio)

            # Update stream metrics
            self.stream_metrics[stream_id] = {
                'last_updated': datetime.now(),
                'quality_metrics': quality_metrics,
                'is_speech': is_speech
            }

            return {
                'stream_id': stream_id,
                'is_speech': is_speech,
                'quality_metrics': quality_metrics,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing audio chunk for stream {stream_id}: {e}")
            return None

    async def get_combined_audio(self) -> Optional[np.ndarray]:
        """Get combined audio from all active streams"""
        try:
            return self.audio_buffer.get_combined_audio()
        except Exception as e:
            logger.error(f"Error getting combined audio: {e}")
            return None

    async def remove_stream(self, stream_id: str):
        """Remove a stream and clean up its resources"""
        try:
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['is_active'] = False
                self.audio_buffer.remove_stream(stream_id)
                if stream_id in self.stream_metrics:
                    del self.stream_metrics[stream_id]
                logger.info(f"Removed stream: {stream_id}")
        except Exception as e:
            logger.error(f"Error removing stream {stream_id}: {e}")

    def get_stream_status(self, stream_id: str) -> Optional[dict]:
        """Get current status of a stream"""
        if stream_id not in self.active_streams:
            return None

        return {
            **self.active_streams[stream_id],
            'metrics': self.stream_metrics.get(stream_id, {}),
            'buffer_status': self.audio_buffer.get_buffer_status().get(stream_id, {})
        }

    def get_all_stream_statuses(self) -> Dict[str, dict]:
        """Get status of all streams"""
        return {
            stream_id: self.get_stream_status(stream_id)
            for stream_id in self.active_streams.keys()
        }