// This is a simple test script to simulate browser audio capture
async function testBrowserAudioCapture() {
    const ws = new WebSocket('ws://localhost:8000/ws/test-browser');
    
    try {
        // Get both microphone and system audio
        const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const systemStream = await navigator.mediaDevices.getDisplayMedia({ 
            audio: true,
            video: false
        });

        // Create audio context
        const audioContext = new AudioContext();
        const micSource = audioContext.createMediaStreamSource(micStream);
        const systemSource = audioContext.createMediaStreamSource(systemStream);
        
        // Create processors
        const micProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        const systemProcessor = audioContext.createScriptProcessor(4096, 1, 1);

        // Handle microphone audio
        micProcessor.onaudioprocess = (e) => {
            if (ws.readyState === WebSocket.OPEN) {
                const audioData = e.inputBuffer.getChannelData(0);
                ws.send(new Float32Array(audioData));
            }
        };

        // Handle system audio
        systemProcessor.onaudioprocess = (e) => {
            if (ws.readyState === WebSocket.OPEN) {
                const audioData = e.inputBuffer.getChannelData(0);
                ws.send(JSON.stringify({
                    type: 'system_audio',
                    audio: Array.from(audioData)
                }));
            }
        };

        // Connect processors
        micSource.connect(micProcessor);
        systemSource.connect(systemProcessor);
        micProcessor.connect(audioContext.destination);
        systemProcessor.connect(audioContext.destination);

        // Handle WebSocket messages
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
        };

        // Cleanup on close
        ws.onclose = () => {
            micStream.getTracks().forEach(track => track.stop());
            systemStream.getTracks().forEach(track => track.stop());
            micProcessor.disconnect();
            systemProcessor.disconnect();
            audioContext.close();
        };

    } catch (error) {
        console.error('Error:', error);
    }
}

// Run the test
testBrowserAudioCapture().catch(console.error);