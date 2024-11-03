import requests
import logging
from datetime import datetime, UTC
import json
import sys
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        logger.info(f"Health Check Response: {response.json()}")
        assert response.status_code == 200
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def test_create_meeting():
    """Test creating a new meeting"""
    try:
        meeting_data = {
            "meeting_id": str(uuid.uuid4()),
            "title": "Test Meeting"
        }
        response = requests.post(f"{BASE_URL}/meetings/", json=meeting_data)
        if not response.ok:
            logger.error(f"Create meeting failed with status {response.status_code}: {response.text}")
            return None
        
        data = response.json()
        logger.info(f"Create Meeting Response: {data}")
        return data
    except Exception as e:
        logger.error(f"Create meeting failed: {e}")
        return None

def test_get_meetings():
    """Test getting all meetings"""
    try:
        response = requests.get(f"{BASE_URL}/meetings")
        if not response.ok:
            logger.error(f"Get meetings failed with status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        logger.info(f"Get Meetings Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Get meetings failed: {e}")
        return None

def test_get_meeting(meeting_id: int):
    """Test getting a specific meeting"""
    try:
        response = requests.get(f"{BASE_URL}/meetings/{meeting_id}")
        if not response.ok:
            logger.error(f"Get meeting failed with status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        logger.info(f"Get Meeting Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Get meeting failed: {e}")
        return None

def test_create_action_item(meeting_id: int):
    """Test creating an action item"""
    try:
        action_item_data = {
            "description": "Test action item",
            "assigned_to": "Tester"
        }
        response = requests.post(
            f"{BASE_URL}/meetings/{meeting_id}/action-items",
            json=action_item_data
        )
        if not response.ok:
            logger.error(f"Create action item failed with status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        logger.info(f"Create Action Item Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Create action item failed: {e}")
        return None

def main():
    logger.info("\n🏃 Running simplified API tests...\n")

    # Wait for server to be ready
    time.sleep(2)

    # Test health endpoint
    logger.info("Testing health endpoint...")
    if test_health_endpoint():
        logger.info("✅ Health endpoint test passed")
    else:
        logger.error("❌ Health endpoint test failed")
        return

    # Test creating a meeting
    logger.info("\nTesting meeting creation...")
    meeting = test_create_meeting()
    if meeting:
        logger.info("✅ Meeting creation test passed")
        meeting_id = meeting.get('id')

        # Test getting all meetings
        logger.info("\nTesting get all meetings...")
        meetings = test_get_meetings()
        if meetings is not None:
            logger.info("✅ Get meetings test passed")
        else:
            logger.error("❌ Get meetings test failed")

        # Test getting specific meeting
        if meeting_id:
            logger.info("\nTesting get specific meeting...")
            meeting_details = test_get_meeting(meeting_id)
            if meeting_details:
                logger.info("✅ Get specific meeting test passed")
            else:
                logger.error("❌ Get specific meeting test failed")

            # Test creating action item
            logger.info("\nTesting action item creation...")
            action_item = test_create_action_item(meeting_id)
            if action_item:
                logger.info("✅ Action item creation test passed")
            else:
                logger.error("❌ Action item creation test failed")
    else:
        logger.error("❌ Meeting creation test failed")

if __name__ == "__main__":
    main()