import numpy as np
from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AudioBuffer:
    def __init__(self, buffer_size: int = 4096, channels: int = 1, sample_rate: int = 16000):
        self.buffer_size = buffer_size
        self.channels = channels
        self.sample_rate = sample_rate
        self.buffer: Dict[str, np.ndarray] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.max_delay = timedelta(milliseconds=150)  # Maximum allowed delay between streams

    def add_stream(self, stream_id: str):
        """Initialize a new audio stream buffer"""
        self.buffer[stream_id] = np.zeros((0, self.channels), dtype=np.float32)
        self.timestamps[stream_id] = datetime.now()
        logger.info(f"Added new audio stream: {stream_id}")

    def add_audio(self, stream_id: str, audio_data: np.ndarray):
        """Add audio data to a specific stream buffer"""
        if stream_id not in self.buffer:
            self.add_stream(stream_id)

        self.buffer[stream_id] = np.vstack([self.buffer[stream_id], audio_data])
        self.timestamps[stream_id] = datetime.now()

    def get_combined_audio(self) -> Optional[np.ndarray]:
        """Combine audio from all active streams"""
        if not self.buffer:
            return None

        # Remove stale streams
        current_time = datetime.now()
        stale_streams = [
            stream_id for stream_id, timestamp in self.timestamps.items()
            if current_time - timestamp > self.max_delay
        ]
        for stream_id in stale_streams:
            del self.buffer[stream_id]
            del self.timestamps[stream_id]
            logger.warning(f"Removed stale stream: {stream_id}")

        if not self.buffer:
            return None

        # Find minimum length across all buffers
        min_length = min(buf.shape[0] for buf in self.buffer.values())
        
        # Combine streams
        combined = np.zeros((min_length, self.channels), dtype=np.float32)
        for stream_id, buf in self.buffer.items():
            combined += buf[:min_length]
            # Keep remaining audio
            self.buffer[stream_id] = buf[min_length:]

        # Normalize
        if np.max(np.abs(combined)) > 1.0:
            combined = combined / np.max(np.abs(combined))

        return combined

    def clear(self):
        """Clear all buffers"""
        self.buffer.clear()
        self.timestamps.clear()

    def remove_stream(self, stream_id: str):
        """Remove a specific stream"""
        if stream_id in self.buffer:
            del self.buffer[stream_id]
            del self.timestamps[stream_id]
            logger.info(f"Removed audio stream: {stream_id}")

    def get_buffer_status(self) -> Dict[str, dict]:
        """Get status of all buffers"""
        return {
            stream_id: {
                "samples": buf.shape[0],
                "duration": buf.shape[0] / self.sample_rate,
                "last_updated": timestamp.isoformat()
            }
            for stream_id, (buf, timestamp) in 
            zip(self.buffer.keys(), zip(self.buffer.values(), self.timestamps.values()))
        }