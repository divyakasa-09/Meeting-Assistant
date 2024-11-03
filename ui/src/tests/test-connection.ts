const testWebSocket = async () => {
    try {
        const ws = new WebSocket('ws://localhost:8000/ws/test-client');
        
        ws.onopen = () => {
            console.log('WebSocket connection established');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        // Keep connection open for a few seconds
        await new Promise(resolve => setTimeout(resolve, 5000));
        ws.close();
        
    } catch (error) {
        console.error('Test failed:', error);
    }
};

const testAPI = async () => {
    try {
        // Test health endpoint
        const healthResponse = await fetch('http://localhost:8000/health');
        console.log('Health check:', await healthResponse.json());
        
        // Test getting meetings
        const meetingsResponse = await fetch('http://localhost:8000/meetings');
        console.log('Meetings:', await meetingsResponse.json());
        
    } catch (error) {
        console.error('API test failed:', error);
    }
};

// Run tests
const runTests = async () => {
    console.log('Testing WebSocket connection...');
    await testWebSocket();
    
    console.log('\nTesting REST API...');
    await testAPI();
};

runTests();