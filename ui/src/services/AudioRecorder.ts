export class AudioRecorder {
    private mediaRecorder: MediaRecorder | null = null;
    private stream: MediaStream | null = null;
    private websocket: WebSocket | null = null;
    private clientId: string;
    private onTranscriptCallback: ((text: string) => void) | null = null;
  
    constructor() {
      this.clientId = crypto.randomUUID();
    }
  
    async startRecording(onTranscript: (text: string) => void): Promise<void> {
      try {
        this.onTranscriptCallback = onTranscript;
        
        // Request audio with specific constraints
        this.stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,          // Mono audio
            sampleRate: 16000,        // 16 kHz sample rate
            echoCancellation: true,   // Enable echo cancellation
            noiseSuppression: true,   // Enable noise suppression
          }
        });
  
        // Connect to WebSocket with client ID
        this.websocket = new WebSocket(`ws://localhost:8000/ws/${this.clientId}`);
        
        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'transcript' && this.onTranscriptCallback) {
              this.onTranscriptCallback(data.text);
            } else if (data.type === 'error') {
              console.error('Server error:', data.message);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
  
        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
  
        // Create MediaRecorder with specific MIME type
        this.mediaRecorder = new MediaRecorder(this.stream, {
          mimeType: 'audio/webm;codecs=opus'
        });
        
        this.mediaRecorder.ondataavailable = async (event) => {
          if (event.data.size > 0 && this.websocket?.readyState === WebSocket.OPEN) {
            // Convert to raw audio data before sending
            const arrayBuffer = await event.data.arrayBuffer();
            this.websocket.send(arrayBuffer);
          }
        };
  
        // Start recording with smaller time slices
        this.mediaRecorder.start(500); // Capture every 500ms
        
      } catch (error) {
        console.error('Error starting recording:', error);
        throw error;
      }
    }
  
    stopRecording(): void {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
      }
  
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
        this.stream = null;
      }
  
      if (this.websocket) {
        this.websocket.close();
        this.websocket = null;
      }
  
      this.onTranscriptCallback = null;
    }
  
    isRecording(): boolean {
      return this.mediaRecorder?.state === 'recording';
    }
  }