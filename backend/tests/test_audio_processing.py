import asyncio
import websockets
import json
import wave
import sys
import os
from datetime import datetime
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def wait_for_server(uri: str, timeout: int = 30, interval: int = 2):
    """Wait for server to become available"""
    start_time = time.time()
    while True:
        try:
            async with websockets.connect(uri) as ws:
                logger.info("Successfully connected to server")
                return True
        except Exception:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Server at {uri} not available after {timeout} seconds")
            logger.info(f"Server not ready, retrying in {interval} seconds...")
            await asyncio.sleep(interval)

async def test_audio_processing(websocket_uri: str, audio_file: str):
    """Test audio processing with a WAV file"""
    try:
        logger.info(f"Connecting to WebSocket at {websocket_uri}")
        
        # Wait for server to be available
        await wait_for_server(websocket_uri)

        # Connect to WebSocket
        async with websockets.connect(websocket_uri) as websocket:
            logger.info("Connected successfully")

            # Receive initial connection message
            response = await websocket.recv()
            logger.info(f"Received initial message: {response}")

            # Check if audio file exists
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                # Create a test audio file if it doesn't exist
                await create_test_audio_file(audio_file)

            # Read and send audio file
            with wave.open(audio_file, 'rb') as wav_file:
                while True:
                    chunk = wav_file.readframes(4096)  # Read 4KB chunks
                    if not chunk:
                        break
                    
                    # Send audio chunk
                    await websocket.send(chunk)
                    logger.debug(f"Sent chunk of size {len(chunk)} bytes")
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(response)
                        
                        if data["type"] == "transcript":
                            logger.info(f"Transcript: {data['text']}")
                            if data.get("speakers"):
                                logger.info(f"Speakers: {data['speakers']}")
                        elif data["type"] == "error":
                            logger.error(f"Error from server: {data['message']}")
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for server response")
                        continue

    except websockets.exceptions.ConnectionClosed:
        logger.error("WebSocket connection closed unexpectedly")
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise

async def create_test_audio_file(filename: str, duration: float = 3.0):
    """Create a test WAV file with a simple tone"""
    import numpy as np
    
    # Audio parameters
    sample_rate = 16000
    frequency = 440  # Hz
    num_samples = int(duration * sample_rate)
    
    # Generate a simple sine wave
    t = np.linspace(0, duration, num_samples)
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    logger.info(f"Created test audio file: {filename}")

async def main():
    # Test configuration
    test_dir = os.path.dirname(os.path.abspath(__file__))
    audio_file = os.path.join(test_dir, "test_audio.wav")
    websocket_uri = "ws://localhost:8000/ws/test-client"

    try:
        # Ensure the server is running
        server_cmd = "uvicorn app.main:app --reload"
        logger.info(f"Make sure the server is running with: {server_cmd}")
        logger.info("Testing audio processing...")
        
        await test_audio_processing(websocket_uri, audio_file)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        logger.info("\nPlease ensure:")
        logger.info("1. The FastAPI server is running")
        logger.info("2. The server is accessible at localhost:8000")
        logger.info("3. The test audio file is available or can be created")
        sys.exit(1)

if __name__ == "__main__":
    # Create and run event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"\nTest failed: {str(e)}")