
interface TranscriptMessage {
    type: 'transcript';
    text: string;
    is_final: boolean;
    audioType: 'microphone' | 'system';
    confidence?: number;
}

interface StatusMessage {
    type: 'status';
    message: string;
}

interface ErrorMessage {
    type: 'error';
    message: string;
}

type WebSocketMessage = TranscriptMessage | StatusMessage | ErrorMessage;

export class AudioRecorder {
    private audioContext: AudioContext | null = null;
    private micProcessor: ScriptProcessorNode | null = null;
    private sysProcessor: ScriptProcessorNode | null = null;
    private micStream: MediaStream | null = null;
    private systemStream: MediaStream | null = null;
    private websocket: WebSocket | null = null;
    private clientId: string;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private isProcessingAudio: boolean = false;
    private messageHandler: ((data: WebSocketMessage) => void) | null = null;
    private isConnected: boolean = false;
    private readonly SILENCE_THRESHOLD = 0.005;
    private readonly BUFFER_SIZE = 4096;
    private lastAudioTypes: Map<string, string> = new Map(); // Track audio types

    constructor(meetingId: string) {
        console.log('AudioRecorder constructor', { meetingId });
        this.clientId = meetingId;
    }

    async startRecording(): Promise<void> {
        try {
            console.log('Starting recording process...');
            this.isProcessingAudio = true;
            await this.initializeWebSocket();
            await this.waitForConnection();
            await this.initializeAudioContext();
            await this.initializeMicrophone();
            await this.initializeSystemAudio();
            console.log('Audio processing setup complete');
        } catch (error) {
            console.error('Error in startRecording:', error);
            await this.cleanup();
            throw error;
        }
    }

    private async initializeAudioContext(): Promise<void> {
        try {
            console.log('Initializing AudioContext...');
            this.audioContext = new AudioContext({
                sampleRate: 16000,
                latencyHint: 'interactive'
            });
        } catch (error) {
            console.error('Error initializing audio context:', error);
            throw error;
        }
    }

    private async initializeMicrophone(): Promise<void> {
        try {
            console.log('Requesting microphone access...');
            this.micStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000,
                    autoGainControl: true,
                    advanced: [{
                        echoCancellation: { ideal: true },
                        noiseSuppression: { ideal: true },
                        autoGainControl: { ideal: true }
                    }]
                } as MediaTrackConstraints
            });

            if (this.audioContext && this.micStream) {
                const micSource = this.audioContext.createMediaStreamSource(this.micStream);
                const processor = this.audioContext.createScriptProcessor(this.BUFFER_SIZE, 1, 1);
                
                const compressor = this.audioContext.createDynamicsCompressor();
                compressor.threshold.value = -50;
                compressor.knee.value = 40;
                compressor.ratio.value = 12;
                compressor.attack.value = 0;
                compressor.release.value = 0.25;

                const gainNode = this.audioContext.createGain();
                gainNode.gain.value = 1.5;

                micSource
                    .connect(compressor)
                    .connect(gainNode)
                    .connect(processor);
                
                processor.onaudioprocess = this.createAudioProcessor('microphone');
                processor.connect(this.audioContext.destination);
                
                this.micProcessor = processor;
                console.log('Microphone processing started');
            }
        } catch (error) {
            console.error('Error initializing microphone:', error);
            throw error;
        }
    }

    private async initializeSystemAudio(): Promise<void> {
        try {
            console.log('Requesting system audio access...');
            const displayStream = await navigator.mediaDevices.getDisplayMedia({
                video: { width: 1, height: 1 },
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000,
                    autoGainControl: true
                } as MediaTrackConstraints
            });

            const audioTrack = displayStream.getAudioTracks()[0];
            if (audioTrack) {
                this.systemStream = new MediaStream([audioTrack]);
                displayStream.getVideoTracks().forEach(track => track.stop());

                if (this.audioContext) {
                    const sysSource = this.audioContext.createMediaStreamSource(this.systemStream);
                    const processor = this.audioContext.createScriptProcessor(this.BUFFER_SIZE, 1, 1);
                    
                    const compressor = this.audioContext.createDynamicsCompressor();
                    compressor.threshold.value = -50;
                    compressor.knee.value = 40;
                    compressor.ratio.value = 12;
                    compressor.attack.value = 0;
                    compressor.release.value = 0.25;

                    const gainNode = this.audioContext.createGain();
                    gainNode.gain.value = 1.5;

                    sysSource
                        .connect(compressor)
                        .connect(gainNode)
                        .connect(processor);
                    
                    processor.onaudioprocess = this.createAudioProcessor('system');
                    processor.connect(this.audioContext.destination);
                    
                    this.sysProcessor = processor;
                    console.log('System audio processing started');
                }
            }
        } catch (error) {
            console.error('Error initializing system audio:', error);
            throw error;
        }
    }

    private createAudioProcessor(type: 'microphone' | 'system'): (this: ScriptProcessorNode, ev: AudioProcessingEvent) => void {
        let consecutiveSilentChunks = 0;
        const MAX_SILENT_CHUNKS = 10;
        let lastProcessTime = Date.now();
        const PROCESS_INTERVAL = 50;
        let lastSentSilence = false;

        return (e: AudioProcessingEvent) => {
            if (!this.isProcessingAudio || !this.websocket) return;

            try {
                const currentTime = Date.now();
                if (currentTime - lastProcessTime < PROCESS_INTERVAL) {
                    return;
                }
                lastProcessTime = currentTime;

                if (this.websocket.readyState === WebSocket.OPEN) {
                    const inputData = e.inputBuffer.getChannelData(0);
                    const maxLevel = Math.max(...Array.from(inputData).map(Math.abs));
                    
                    if (maxLevel > this.SILENCE_THRESHOLD) {
                        const int16Array = new Int16Array(inputData.length);
                        
                        for (let i = 0; i < inputData.length; i++) {
                            const s = Math.max(-1, Math.min(1, inputData[i] * 1.2));
                            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }

                        this.lastAudioTypes.set('current', type);

                        console.log(`Processing ${type} audio with level:`, maxLevel);

                        this.websocket.send(JSON.stringify({
                            type: 'audio_meta',
                            audioType: type,
                            sampleRate: this.audioContext?.sampleRate || 16000,
                            timestamp: Date.now(),
                            level: maxLevel,
                            source: type
                        }));

                        this.websocket.send(int16Array.buffer);
                        consecutiveSilentChunks = 0;
                        lastSentSilence = false;
                    } else {
                        consecutiveSilentChunks++;
                        
                        if (consecutiveSilentChunks >= MAX_SILENT_CHUNKS && !lastSentSilence) {
                            console.log(`Silence detected for ${type}`);
                            this.websocket.send(JSON.stringify({
                                type: 'audio_meta',
                                audioType: type,
                                sampleRate: this.audioContext?.sampleRate || 16000,
                                timestamp: Date.now(),
                                isSilence: true,
                                source: type
                            }));
                            lastSentSilence = true;
                        }
                    }
                }
            } catch (error) {
                console.error(`[${type}] Error processing audio:`, error);
            }
        };
    }

    private async waitForConnection(): Promise<void> {
        console.log('Waiting for WebSocket connection...');
        return new Promise((resolve, reject) => {
            const checkConnection = () => {
                if (this.isConnected) {
                    console.log('WebSocket connected');
                    resolve();
                } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    reject(new Error('Failed to establish WebSocket connection'));
                } else {
                    setTimeout(checkConnection, 100);
                }
            };
            checkConnection();
        });
    }

    private async initializeWebSocket(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            try {
                console.log('Initializing WebSocket...', { clientId: this.clientId });
                this.websocket = new WebSocket(`ws://localhost:8000/ws/${this.clientId}`);
                
                this.websocket.onopen = () => {
                    console.log('WebSocket connected successfully');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    resolve();
                };
                
                this.websocket.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };

                this.websocket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data) as WebSocketMessage;
                        console.log('Received WebSocket message:', {
                            type: data.type,
                            isFinal: 'is_final' in data ? data.is_final : undefined,
                            text: 'text' in data ? data.text?.substring(0, 50) + '...' : undefined,
                            audioType: 'audioType' in data ? data.audioType : undefined
                        });

                        if (data.type === 'transcript' && 'audioType' in data) {
                            const lastKnownType = this.lastAudioTypes.get('current');
                            if (lastKnownType && data.audioType !== lastKnownType) {
                                console.warn('Audio type mismatch:', {
                                    received: data.audioType,
                                    expected: lastKnownType
                                });
                            }
                        }

                        if (this.messageHandler) {
                            this.messageHandler(data);
                        }
                    } catch (error) {
                        console.error('Error processing WebSocket message:', error);
                    }
                };

                this.websocket.onclose = () => {
                    console.log('WebSocket connection closed');
                    this.isConnected = false;
                    if (this.isProcessingAudio) {
                        this.handleWebSocketReconnect();
                    }
                };
            } catch (error) {
                console.error('Error initializing WebSocket:', error);
                reject(error);
            }
        });
    }

    private async handleWebSocketReconnect(): Promise<void> {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            await new Promise(resolve => setTimeout(resolve, 1000));
            await this.initializeWebSocket();
        } else {
            console.error('Max reconnection attempts reached');
            await this.cleanup();
        }
    }

    setMessageHandler(handler: (data: WebSocketMessage) => void): void {
        console.log('Setting message handler');
        this.messageHandler = handler;
    }

    async stopRecording(): Promise<void> {
        try {
            console.log('Stopping recording...');
            await this.cleanup();
        } catch (error) {
            console.error('Error in stopRecording:', error);
            throw error;
        }
    }

    private async cleanup(): Promise<void> {
        console.log('Starting cleanup...');
        this.isProcessingAudio = false;
        
        try {
            if (this.micProcessor) {
                this.micProcessor.disconnect();
                this.micProcessor = null;
                console.log('Disconnected microphone processor');
            }

            if (this.sysProcessor) {
                this.sysProcessor.disconnect();
                this.sysProcessor = null;
                console.log('Disconnected system processor');
            }

            if (this.micStream) {
                this.micStream.getTracks().forEach(track => track.stop());
                this.micStream = null;
                console.log('Stopped microphone stream');
            }

            if (this.systemStream) {
                this.systemStream.getTracks().forEach(track => track.stop());
                this.systemStream = null;
                console.log('Stopped system stream');
            }

            if (this.audioContext?.state !== 'closed') {
                await this.audioContext?.close();
                this.audioContext = null;
                console.log('Closed audio context');
            }

            if (this.websocket?.readyState === WebSocket.OPEN) {
                this.websocket.close();
                console.log('Closed WebSocket connection');
            }
            this.websocket = null;
            this.isConnected = false;
            this.lastAudioTypes.clear();
            
            console.log('Cleanup complete');
        } catch (error) {
            console.error('Error during cleanup:', error);
            throw error;
        }
    }
}