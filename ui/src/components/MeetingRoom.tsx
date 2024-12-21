import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from './ui/button';
import { AudioRecorder } from '../services/AudioRecorder';

interface MeetingRoomProps {
  onBack: () => void;
  meetingId: string;
  meetingTitle?: string;
}

interface TranscriptItem {
  type: 'microphone' | 'system';
  text: string;
  timestamp?: string;
}

interface InterimTranscripts {
  microphone?: string;
  system?: string;
}

export function MeetingRoom({ onBack, meetingId, meetingTitle }: MeetingRoomProps) {
  // State management
  const [isRecording, setIsRecording] = useState(false);
  const [transcripts, setTranscripts] = useState<TranscriptItem[]>([]);
  const [interimTranscripts, setInterimTranscripts] = useState<InterimTranscripts>({});
  const [status, setStatus] = useState<string>('');
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [actionItems, setActionItems] = useState<string[]>([]);
  const [summary, setSummary] = useState<string>('');

  // Refs
  const recorderRef = useRef<AudioRecorder | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    console.log('MeetingRoom mounted with meetingId:', meetingId);
    mountedRef.current = true;

    return () => {
      console.log('MeetingRoom component cleanup');
      mountedRef.current = false;
      cleanup();
    };
  }, [meetingId]);

  const cleanup = useCallback(() => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
    if (recorderRef.current) {
      recorderRef.current.stopRecording();
      recorderRef.current = null;
    }
  }, []);

  // Duration timer effect
  useEffect(() => {
    if (!mountedRef.current) return;

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

  // Auto-scroll effect
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [transcripts, interimTranscripts]);

  // Styling functions
  const getTranscriptStyle = () => {
    return 'text-gray-700 font-medium bg-gray-50 rounded-lg px-3 py-2';
  };


  const getInterimStyle = () => {
    return 'text-gray-400 italic bg-gray-50/50 rounded-lg px-3 py-2';
  };

  const startRecording = async () => {
    try {
      setError(null);
      setStatus('Requesting audio access...');

      if (!meetingId) {
        throw new Error('No meeting ID provided');
      }

      const recorder = new AudioRecorder(meetingId);

      recorder.setMessageHandler((data) => {
        if (!mountedRef.current) return;

        if (data.type === 'transcript') {
          const audioType = data.audioType as 'microphone' | 'system';
          
          // Only process if there's actual text content
          if (data.text && data.text.trim()) {
            if (data.is_final) {
              setTranscripts(prev => [...prev, {
                type: audioType,
                text: data.text.trim(),
                timestamp: new Date().toISOString()
              }]);

              // Clear interim transcript for this source
              setInterimTranscripts(prev => ({
                ...prev,
                [audioType]: undefined
              }));
            } else {
              // Only update interim if text has changed significantly
              setInterimTranscripts(prev => {
                const currentText = prev[audioType];
                const newText = data.text.trim();
                if (currentText !== newText) {
                  return {
                    ...prev,
                    [audioType]: newText
                  };
                }
                return prev;
              });
            }
          }
        } else if (data.type === 'status') {
          setStatus(data.message);
        } else if (data.type === 'error') {
          console.error('Server error:', data.message);
          setError(data.message);
        }
      });

      await recorder.startRecording();
      recorderRef.current = recorder;
      setIsRecording(true);
      setStatus('Recording in progress...');

    } catch (error) {
      console.error('Error in startRecording:', error);
      setStatus('Failed to start recording');
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
      setIsRecording(false);
      cleanup();
    }
  };

  const stopRecording = async () => {
    try {
      if (recorderRef.current) {
        await recorderRef.current.stopRecording();
        recorderRef.current = null;
      }
      setIsRecording(false);
      setStatus('Recording stopped');

      if (transcripts.length > 0) {
        const summaryText = `Meeting lasted ${formatTime(duration)}. ${transcripts.length} segments were recorded.`;
        setSummary(summaryText);
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      setError('Failed to stop recording properly');
    }
  };

  const handleEndMeeting = async () => {
    try {
      await stopRecording();
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
            onClick={() => isRecording ? stopRecording() : startRecording()}
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
            <div className="space-y-3">
             {transcripts.map((transcript, index) => (
  transcript.text && transcript.text.trim() && (
    <div
      key={`final-${index}`}
      className={getTranscriptStyle()}
    >
      {transcript.text}
    </div>
  )
))}
              {/* Interim Transcripts */}
              {interimTranscripts.system && (
  <div className={getInterimStyle()}>
    {interimTranscripts.system}
  </div>
)}
{interimTranscripts.microphone && (
  <div className={getInterimStyle()}>
    {interimTranscripts.microphone}
  </div>
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