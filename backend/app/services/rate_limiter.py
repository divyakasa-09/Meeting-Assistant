from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = deque()
    
    def can_make_request(self) -> bool:
        now = datetime.now()
        
        # Remove requests older than 1 minute
        while self.requests and self.requests[0] < now - timedelta(minutes=1):
            self.requests.popleft()
        
        # Check if we can make a new request
        if len(self.requests) < self.requests_per_minute:
            self.requests.append(now)
            return True
            
        return False