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
        this.stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            channelCount: 1,
            sampleRate: 16000
          } 
        });
  
        // Connect to WebSocket
        this.websocket = new WebSocket(`ws://localhost:8000/ws/${this.clientId}`);
        
        this.websocket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'transcript' && this.onTranscriptCallback) {
            this.onTranscriptCallback(data.text);
          }
        };
  
        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
  
        // Create MediaRecorder
        this.mediaRecorder = new MediaRecorder(this.stream);
        
        this.mediaRecorder.ondataavailable = async (event) => {
          if (event.data.size > 0 && this.websocket?.readyState === WebSocket.OPEN) {
            // Convert blob to array buffer and send
            const arrayBuffer = await event.data.arrayBuffer();
            this.websocket.send(arrayBuffer);
          }
        };
  
        this.mediaRecorder.start(1000); // Collect data every second
        
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