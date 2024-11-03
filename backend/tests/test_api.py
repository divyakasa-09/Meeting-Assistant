import asyncio
import websockets
import json
import requests
from datetime import datetime, UTC
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def test_websocket_connection():
    """Test WebSocket connection and audio streaming"""
    client_id = "test-client-1"
    uri = f"{WS_URL}/{client_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket connection established")
            
            # Wait for connection message
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received: {response_data}")
            
            # Simulate sending some audio data
            dummy_audio_data = b"dummy audio data"
            await websocket.send(dummy_audio_data)
            
            # Wait for transcription response
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received transcription: {response_data}")
            
            return True
            
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")
        return False

def test_rest_endpoints():
    """Test REST API endpoints"""
    try:
        # Test health check endpoint
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        logger.info("✅ Health check endpoint working")
        
        # Create a new meeting
        meeting_data = {
            "title": "API Test Meeting",
            "meeting_id": "test-meeting-api-1"
        }
        response = requests.post(f"{BASE_URL}/meetings/", json=meeting_data)
        assert response.status_code == 200
        meeting = response.json()
        meeting_id = meeting["id"]
        logger.info(f"✅ Created meeting with ID: {meeting_id}")
        
        # Add an action item
        action_item_data = {
            "description": "Test action from API",
            "assigned_to": "API Tester",
            "due_date": datetime.now(UTC).isoformat()
        }
        response = requests.post(
            f"{BASE_URL}/meetings/{meeting_id}/action-items",
            json=action_item_data
        )
        assert response.status_code == 200
        logger.info("✅ Created action item")
        
        # Add a summary
        summary_data = {
            "summary_text": "This is a test summary from API"
        }
        response = requests.post(
            f"{BASE_URL}/summaries/",
            params={"meeting_id": meeting_id},
            json=summary_data
        )
        assert response.status_code == 200
        logger.info("✅ Created summary")
        
        # Get meeting details
        response = requests.get(f"{BASE_URL}/meetings/{meeting_id}")
        assert response.status_code == 200
        meeting_details = response.json()
        logger.info("✅ Retrieved meeting details")
        logger.info(f"Meeting details: {json.dumps(meeting_details, indent=2)}")
        
        # End the meeting
        response = requests.put(f"{BASE_URL}/meetings/{meeting_id}/end")
        assert response.status_code == 200
        logger.info("✅ Ended meeting")
        
        return True
        
    except AssertionError as e:
        logger.error(f"API test failed with assertion error: {e}")
        return False
    except Exception as e:
        logger.error(f"API test failed with error: {e}")
        return False

async def run_all_tests():
    logger.info("\n🏃 Running API tests...\n")
    
    # Test WebSocket
    logger.info("Testing WebSocket connection...")
    ws_success = await test_websocket_connection()
    if ws_success:
        logger.info("✅ WebSocket tests passed")
    else:
        logger.error("❌ WebSocket tests failed")
    
    # Test REST endpoints
    logger.info("\nTesting REST endpoints...")
    rest_success = test_rest_endpoints()
    if rest_success:
        logger.info("✅ REST API tests passed")
    else:
        logger.error("❌ REST API tests failed")

if __name__ == "__main__":
    asyncio.run(run_all_tests())