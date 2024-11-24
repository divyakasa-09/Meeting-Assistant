export class AudioRecorder {
  private micRecorder: MediaRecorder | null = null;
  private systemRecorder: MediaRecorder | null = null;
  private micStream: MediaStream | null = null;
  private systemStream: MediaStream | null = null;
  private websocket: WebSocket | null = null;
  private clientId: string;
  private onTranscriptCallback: ((text: string, type: 'microphone' | 'system') => void) | null = null;

  constructor() {
    this.clientId = crypto.randomUUID();
  }

  async startRecording(onTranscript: (text: string, type: 'microphone' | 'system') => void): Promise<void> {
    try {
      this.onTranscriptCallback = onTranscript;

      // Request microphone and system audio streams
      this.micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const displayStream = await navigator.mediaDevices.getDisplayMedia({ audio: true });
      const audioTrack = displayStream.getAudioTracks()[0];
      this.systemStream = new MediaStream([audioTrack]);

      // Initialize WebSocket
      this.websocket = new WebSocket(`ws://localhost:8000/ws/${this.clientId}`);
      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'transcript' && this.onTranscriptCallback) {
          this.onTranscriptCallback(data.text, data.audioType);
        }
      };

      // Set up recorders for microphone and system audio
      this.setupRecorder(this.micStream, 'microphone');
      if (this.systemStream) {
        this.setupRecorder(this.systemStream, 'system');
      }
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  }

  private setupRecorder(stream: MediaStream, type: 'microphone' | 'system') {
    const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
    recorder.ondataavailable = async (event) => {
      if (this.websocket?.readyState === WebSocket.OPEN && event.data.size > 0) {
        const arrayBuffer = await event.data.arrayBuffer();
        this.websocket.send(JSON.stringify({ type, audio: Array.from(new Uint8Array(arrayBuffer)) }));
      }
    };
    recorder.start(500); // Send chunks every 500ms

    if (type === 'microphone') {
      this.micRecorder = recorder;
    } else {
      this.systemRecorder = recorder;
    }
  }

  stopRecording(): void {
    [this.micRecorder, this.systemRecorder].forEach((recorder) => recorder?.stop());
    [this.micStream, this.systemStream].forEach((stream) =>
      stream?.getTracks().forEach((track) => track.stop())
    );
    this.websocket?.close();
  }
}
