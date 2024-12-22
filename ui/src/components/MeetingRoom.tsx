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

interface MeetingInsights {
  summary?: {
    summary: string;
    topics: string[];
    decisions: string[];
  };
  questions?: string[];
  action_items?: Array<{
    description: string;
    assigned_to?: string;
    priority?: string;
  }>;
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
  const [insights, setInsights] = useState<MeetingInsights>({});

  // Refs
  const recorderRef = useRef<AudioRecorder | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const insightsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  const fetchInsights = useCallback(async () => {
    if (!meetingId || !isRecording) return;

    try {
        console.log('Fetching insights for meeting:', meetingId);
        const response = await fetch(`http://localhost:8000/meetings/${meetingId}/live-insights`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch insights: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Received insights data:', data);

        // Transform questions if needed
        const questions = data.questions ? 
            (Array.isArray(data.questions) ? 
                data.questions : 
                Object.keys(data.questions))
            : [];

        // Transform action items if needed
        const actionItems = data.action_items ? 
            (Array.isArray(data.action_items) ? 
                data.action_items : 
                [data.action_items])
            : [];

        setInsights(prevInsights => ({
            ...prevInsights,
            summary: data.summary || prevInsights.summary,
            questions: questions,
            action_items: actionItems
        }));

    } catch (error) {
        console.error('Error fetching insights:', error);
        setError('Failed to fetch meeting insights');
    }
}, [meetingId, isRecording]);


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
    if (insightsIntervalRef.current) {
      clearInterval(insightsIntervalRef.current);
      insightsIntervalRef.current = null;
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

  // Insights fetching effect
  useEffect(() => {
    if (isRecording && meetingId) {
      // Fetch immediately
      fetchInsights();
      
      // Then fetch every 30 seconds
      insightsIntervalRef.current = setInterval(fetchInsights, 30000);
    }

    return () => {
      if (insightsIntervalRef.current) {
        clearInterval(insightsIntervalRef.current);
        insightsIntervalRef.current = null;
      }
    };
  }, [isRecording, meetingId, fetchInsights]);

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
          
          if (data.text && data.text.trim()) {
            if (data.is_final) {
              setTranscripts(prev => [...prev, {
                type: audioType,
                text: data.text.trim(),
                timestamp: new Date().toISOString()
              }]);

              setInterimTranscripts(prev => ({
                ...prev,
                [audioType]: undefined
              }));
            } else {
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

      // if (transcripts.length > 0) {
      //   const summaryText = `Meeting lasted ${formatTime(duration)}. ${transcripts.length} segments were recorded.`;
      //   setSummary(summaryText);
      // }
    } catch (error) {
      console.error('Error stopping recording:', error);
      setError('Failed to stop recording properly');
    }
  };
 // Add this near your other useEffect hooks
useEffect(() => {
  console.log('Action items updated:', insights.action_items);
  console.log('Questions updated:', insights.questions);
}, [insights.action_items, insights.questions]);
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
            {insights.summary ? (
              <div className="space-y-4">
                <p className="text-gray-700">{insights.summary.summary}</p>
                {insights.summary.topics?.length > 0 && (
                  <div>
                    <h3 className="font-medium mt-2 mb-1">Key Topics:</h3>
                    <ul className="list-disc pl-4">
                      {insights.summary.topics.map((topic, idx) => (
                        <li key={idx} className="text-gray-600">{topic}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {insights.summary.decisions?.length > 0 && (
                  <div>
                    <h3 className="font-medium mt-2 mb-1">Decisions Made:</h3>
                    <ul className="list-disc pl-4">
                      {insights.summary.decisions.map((decision, idx) => (
                        <li key={idx} className="text-gray-600">{decision}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500">
                {isRecording ? 'Generating summary...' : 'Start recording to see summary'}
              </p>
            )}
          </div>

      
          <div className="bg-white rounded-xl border p-6 shadow-sm">
    <h2 className="text-lg font-medium mb-4">Action Items</h2>
    {Array.isArray(insights.action_items) && insights.action_items.length > 0 ? (
       
  <ul className="space-y-2">
    {insights.action_items.map((item, index) => (
      <li key={index} className="text-gray-700 flex items-start gap-2">
        <span>•</span>
        <div>
          <p>{item.description}</p>
          {item.assigned_to && (
            <p className="text-sm text-gray-500">Assigned to: {item.assigned_to}</p>
          )}
          {item.priority && (
            <span className={`text-xs px-2 py-1 rounded ${
              item.priority === 'high' ? 'bg-red-100 text-red-700' :
              item.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
              'bg-green-100 text-green-700'
            }`}>
              {item.priority}
            </span>
          )}
        </div>
      </li>
    ))}
  </ul>
) : (
  <p className="text-gray-500">
    {isRecording ? 'Detecting action items...' : 'Start recording to see action items'}
  </p>
)}

          </div>

    {/* Follow-up Questions Panel */}
    <div className="bg-white rounded-xl border p-6 shadow-sm">
    <h2 className="text-lg font-medium mb-4">Follow-up Questions</h2>
    {Array.isArray(insights.questions) && insights.questions.length > 0 ? (
  <ul className="space-y-2">
    {insights.questions.map((question, index) => (
      <li key={index} className="text-gray-700">
        • {question}
      </li>
    ))}
  </ul>
) : (
  <p className="text-gray-500">
    {isRecording ? 'Generating questions...' : 'Start recording to see suggested questions'}
  </p>
)}

          </div>
        </div>
      </div>
    </div>
  );
}