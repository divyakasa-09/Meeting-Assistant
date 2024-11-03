import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class AudioQualityController:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.noise_threshold = 0.02
        
    def process_audio(self, audio_data: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Process audio data for quality improvement
        Returns: (processed_audio, is_speech)
        """
        try:
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Noise reduction
            audio_data = self._reduce_noise(audio_data)

            # Check if speech is present
            is_speech = self._detect_speech(audio_data)

            # Normalize volume
            audio_data = self._normalize_volume(audio_data)

            return audio_data, is_speech

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return audio_data, False

    def _reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Simple noise reduction"""
        # Calculate noise floor
        noise_floor = np.mean(np.abs(audio_data[audio_data < self.noise_threshold]))
        
        # Apply noise gate
        audio_data[np.abs(audio_data) < noise_floor * 2] = 0
        
        return audio_data

    def _detect_speech(self, audio_data: np.ndarray) -> bool:
        """Detect if audio contains speech using energy levels"""
        try:
            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Calculate zero crossing rate
            zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data)))) / len(audio_data)
            
            # Simple speech detection heuristic
            is_speech = rms > self.noise_threshold and zero_crossings > 0.1
            
            return bool(is_speech)
            
        except Exception as e:
            logger.error(f"Error detecting speech: {e}")
            return True  # Default to true in case of error

    def _normalize_volume(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio volume"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val * 0.9  # Leave some headroom
        return audio_data

    def check_quality(self, audio_data: np.ndarray) -> dict:
        """Check audio quality metrics"""
        return {
            "rms_level": float(np.sqrt(np.mean(audio_data**2))),
            "peak_level": float(np.max(np.abs(audio_data))),
            "has_speech": self._detect_speech(audio_data),
            "zero_crossings": len(np.where(np.diff(np.signbit(audio_data)))[0]),
        }