import { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { MeetingService } from '../services/MeetingService';

interface MeetingRoomProps {
  onBack: () => void;
  meetingId: string;     // UUID string for WebSocket
  meetingTitle?: string;
}

export function MeetingRoom({ onBack, meetingId, meetingTitle }: MeetingRoomProps) {
  // State management
  const [isRecording, setIsRecording] = useState(false);
  const [transcripts, setTranscripts] = useState<{ type: 'microphone' | 'system'; text: string }[]>([]);
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [actionItems, setActionItems] = useState<string[]>([]);
  const [summary, setSummary] = useState<string>('');
  

  // Refs for managing resources
  const streamRef = useRef<MediaStream | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Timer Effect
  useEffect(() => {
    if (isRecording) {
      durationIntervalRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    }

    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [isRecording]);

  // Auto-scroll Effect
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [transcripts, currentTranscript]);

  // Cleanup Effect
  useEffect(() => {
    console.log('MeetingRoom mounted with meetingId:', meetingId);
    return () => {
      stopRecording();
      cleanup();
    };
  }, []);

  const cleanup = () => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (websocketRef.current) {
      websocketRef.current.close();
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
  };

  const startRecording = async () => {
    try {
      setError(null);
      setStatus('Requesting microphone access...');
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
          autoGainControl: true,
        }
      });

      streamRef.current = stream;
      setStatus('Connecting to transcription service...');

      // Initialize WebSocket connection
      const ws = new WebSocket(`ws://localhost:8000/ws/${meetingId}`);
      websocketRef.current = ws;

      ws.onopen = () => {
        setStatus('Connected to transcription service');
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received WebSocket message:', data);
      
          if (data.type === 'transcript') {
            if (data.is_final) {
              setTranscripts((prev) => [
                ...prev,
                { type: data.audioType, text: data.text },
              ]);
              setCurrentTranscript('');
            } else {
              setCurrentTranscript(data.text);
            }
          } else if (data.type === 'status') {
            setStatus(data.message);
          } else if (data.type === 'error') {
            console.error('Server error:', data.message);
            setStatus(`Error: ${data.message}`);
            setError(data.message);
          }
        } catch (error) {
          console.error('Error processing message:', error);
        }
      };
      

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('Connection error occurred');
        setError('Failed to connect to transcription service');
      };

      ws.onclose = () => {
        setStatus('Connection closed');
        setIsRecording(false);
      };

      // Set up audio processing
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (ws.readyState === WebSocket.OPEN) {
          const audioData = e.inputBuffer.getChannelData(0);
          const int16Array = new Int16Array(audioData.length);
          
          for (let i = 0; i < audioData.length; i++) {
            const s = Math.max(-1, Math.min(1, audioData[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          
          ws.send(int16Array.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      setStatus('Recording...');

    } catch (error) {
      console.error('Error starting recording:', error);
      setStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setError(error instanceof Error ? error.message : 'Unknown error');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }

    setIsRecording(false);
    setStatus('Recording stopped');

    // Generate summary from transcripts
    if (transcripts.length > 0) {
      const summaryText = `Meeting lasted ${formatTime(duration)}. ${transcripts.length} segments were recorded.`;
      setSummary(summaryText);
    }
  };

  const handleEndMeeting = async () => {
    try {
      stopRecording();
      onBack();
    } catch (error) {
      console.error('Error ending meeting:', error);
      setError('Failed to end meeting properly');
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-5xl mx-auto p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">
            {meetingTitle || 'Active Meeting'}
          </h1>
          <div className="flex flex-col gap-1">
            <div className="text-gray-500">
              Duration: {formatTime(duration)}
            </div>
            <div className="text-sm text-gray-500">{status}</div>
            {error && (
              <div className="text-sm text-red-500">{error}</div>
            )}
          </div>
        </div>
        <div className="flex gap-4">
          <Button 
            variant="outline" 
            onClick={handleEndMeeting}
          >
            End Meeting
          </Button>
          <Button 
            variant={isRecording ? "destructive" : "default"}
            onClick={() => {
              if (isRecording) {
                stopRecording();
              } else {
                startRecording();
              }
            }}
          >
            {isRecording ? 'Stop Recording' : 'Start Recording'}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Transcript Panel */}
        <div className="md:col-span-2">
          <div className="bg-white rounded-xl border p-6 shadow-sm h-[600px] overflow-y-auto">
            <h2 className="text-lg font-medium mb-4">Live Transcript</h2>
            <div className="space-y-2">
  {transcripts.map((transcript, index) => (
    <p
      key={index}
      className={`text-gray-700 ${
        transcript.type === 'system' ? 'text-blue-500' : ''
      }`}
    >
      [{transcript.type.toUpperCase()}] {transcript.text}
    </p>
  ))}
  {currentTranscript && (
    <p className="text-gray-500 italic">{currentTranscript}</p>
  )}
  <div ref={transcriptEndRef} />
</div>

          </div>
        </div>

        {/* Side Panels */}
        <div className="space-y-6">
          {/* Summary Panel */}
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <h2 className="text-lg font-medium mb-4">Summary</h2>
            <p className="text-gray-700">
              {summary || (isRecording ? 'Generating summary...' : 'Start recording to see summary')}
            </p>
          </div>

          {/* Action Items Panel */}
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <h2 className="text-lg font-medium mb-4">Action Items</h2>
            {actionItems.length > 0 ? (
              <ul className="space-y-2">
                {actionItems.map((item, index) => (
                  <li key={index} className="text-gray-700">
                    • {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">
                {isRecording ? 'Detecting action items...' : 'Start recording to see action items'}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}