import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Meeting } from '../services/MeetingService';
import { X, Clock, User, CheckCircle, AlertCircle, MessageSquare, AlertTriangle } from 'lucide-react';

interface MeetingDetailsProps {
  meeting: Meeting;
  onClose: () => void;
  onDelete: (meetingId: string) => void;
  isOpen: boolean;
}

export function MeetingDetails({ meeting, onClose, onDelete, isOpen }: MeetingDetailsProps) {
  const [activeTab, setActiveTab] = useState<'transcripts' | 'actions' | 'summary' | 'questions'>('transcripts');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('Meeting details changed:', meeting);
    console.log('Transcripts:', meeting?.transcripts);

    if (isOpen && meeting) {
      setLoading(true);
      setError(null);

      const timer = setTimeout(() => {
        try {
          setLoading(false);
        } catch (err) {
          console.error('Error loading meeting data:', err);
          setError(err instanceof Error ? err.message : 'Failed to load meeting data');
          setLoading(false);
        }
      }, 300);

      return () => clearTimeout(timer);
    }
  }, [isOpen, meeting]);

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this meeting?')) {
      onDelete(meeting.meeting_id);
      onClose();
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch (e) {
      console.error('Error formatting date:', e);
      return 'Invalid date';
    }
  };

  const getTotalDuration = () => {
    if (!meeting.start_time) return '0 minutes';
    try {
      const start = new Date(meeting.start_time);
      const end = meeting.end_time ? new Date(meeting.end_time) : new Date();
      const duration = Math.floor((end.getTime() - start.getTime()) / (1000 * 60));
      return `${duration} minutes`;
    } catch (e) {
      console.error('Error calculating duration:', e);
      return 'Duration unavailable';
    }
  };

  const getParticipants = () => {
    const speakers = new Set<string>();
    try {
      if (Array.isArray(meeting.transcripts)) {
        meeting.transcripts.forEach(transcript => {
          if (transcript.speaker) speakers.add(transcript.speaker);
        });
      }
      return Array.from(speakers);
    } catch (e) {
      console.error('Error getting participants:', e);
      return [];
    }
  };

  const getSortedTranscripts = () => {
    try {
      if (!Array.isArray(meeting.transcripts)) {
        console.warn('Transcripts is not an array:', meeting.transcripts);
        return [];
      }
      
      return [...meeting.transcripts].sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeA - timeB;
      });
    } catch (e) {
      console.error('Error sorting transcripts:', e);
      return [];
    }
  };

  const generateSummaryPoints = () => {
    const points = [];
    if (Array.isArray(meeting.transcripts) && meeting.transcripts.length) {
      points.push(`Total Duration: ${getTotalDuration()}`);
      points.push(`${meeting.transcripts.length} conversation points discussed`);
    }
    if (Array.isArray(meeting.action_items) && meeting.action_items.length) {
      points.push(`${meeting.action_items.length} action items identified`);
    }
    const participants = getParticipants();
    if (participants.length) {
      points.push(`${participants.length} participants involved`);
    }
    return points;
  };

  const generateQuestions = () => {
    const questions = [
      "What are the next steps for the discussed items?",
      "Who will be responsible for the action items?",
      "When is the follow-up meeting scheduled?"
    ];

    if (Array.isArray(meeting.action_items)) {
      meeting.action_items.forEach(item => {
        if (item.description) {
          questions.push(`What is the timeline for "${item.description}"?`);
        }
      });
    }

    return questions;
  };

  const renderTranscripts = () => {
    if (error) {
      return (
        <div className="text-center py-8 bg-red-50 rounded-lg border border-red-100">
          <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <p className="text-red-600 font-medium">Error loading transcripts</p>
          <p className="text-red-500 text-sm mt-1">{error}</p>
        </div>
      );
    }
  
    const transcripts = getSortedTranscripts();
  
    if (!Array.isArray(transcripts) || transcripts.length === 0) {
      return (
        <div className="text-center py-8 bg-gray-50 rounded-lg border">
          <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No transcripts available</p>
        </div>
      );
    }
  
    const combinedText = transcripts.map(t => t.text).join(' ');
  
    return (
      <div className="bg-white rounded-lg p-4 shadow-sm border">
        <p className="text-gray-700 whitespace-pre-wrap">{combinedText}</p>
        <div className="mt-4 flex justify-between items-center text-sm text-gray-500">
          <div className="flex items-center">
            <Clock className="h-4 w-4 mr-1" />
            {formatDate(transcripts[0].timestamp)} - {formatDate(transcripts[transcripts.length - 1].timestamp)}
          </div>
        </div>
      </div>
    );
  };

  const renderActionItems = () => {
    if (!Array.isArray(meeting.action_items) || meeting.action_items.length === 0) {
      return (
        <div className="text-center py-8 bg-gray-50 rounded-lg border">
          <CheckCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No action items available</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {meeting.action_items.map((item, index) => (
          <div key={index} className="bg-white rounded-lg p-4 shadow-sm border">
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-blue-500 mt-0.5 mr-2 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-gray-700">{item.description}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {item.assigned_to && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      <User className="h-3 w-3 mr-1" />
                      {item.assigned_to}
                    </span>
                  )}
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    item.status === 'completed' 
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {item.status}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div 
      className={`fixed inset-y-0 right-0 w-[40%] bg-white shadow-xl transform transition-transform duration-300 ease-in-out border-l ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-6 border-b bg-gray-50">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">{meeting.title || 'Untitled Meeting'}</h2>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>
          <div className="mt-2 space-y-1">
            {meeting.start_time && (
              <div className="flex items-center text-sm text-gray-500">
                <Clock className="h-4 w-4 mr-2" />
                Started: {formatDate(meeting.start_time)}
              </div>
            )}
            {meeting.end_time && (
              <div className="flex items-center text-sm text-gray-500">
                <Clock className="h-4 w-4 mr-2" />
                Ended: {formatDate(meeting.end_time)}
              </div>
            )}
            <div className="flex items-center text-sm">
              <AlertCircle className="h-4 w-4 mr-2" />
              <span className={meeting.is_active ? 'text-green-600' : 'text-gray-500'}>
                {meeting.is_active ? 'Active' : 'Ended'}
              </span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b px-6 bg-white">
          {(['transcripts', 'actions', 'summary', 'questions'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          {activeTab === 'transcripts' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Transcripts</h3>
                <span className="text-sm text-gray-500">
                  {Array.isArray(meeting.transcripts) ? meeting.transcripts.length : 0} entries
                </span>
              </div>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : (
                renderTranscripts()
              )}
            </div>
          )}

          {activeTab === 'actions' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Action Items</h3>
                <span className="text-sm text-gray-500">
                  {Array.isArray(meeting.action_items) ? meeting.action_items.length : 0} items
                </span>
              </div>
              {renderActionItems()}
            </div>
          )}

          {activeTab === 'summary' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Meeting Summary</h3>
              <div className="bg-white rounded-lg p-6 shadow-sm border space-y-4">
                <div className="space-y-3">
                  {generateSummaryPoints().map((point, index) => (
                    <div key={index} className="flex items-center">
                      <div className="h-2 w-2 rounded-full bg-blue-500 mr-3"></div>
                      <p className="text-gray-700">{point}</p>
                    </div>
                  ))}
                </div>
                {Array.isArray(meeting.transcripts) && meeting.transcripts.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium mb-2">Key Discussion Points:</h4>
                    <div className="space-y-2">
                      {getSortedTranscripts().slice(-3).map((transcript, index) => (
                        <p key={index} className="text-gray-600 text-sm">• {transcript.text}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'questions' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Follow-up Questions</h3>
              <div className="space-y-3">
                {generateQuestions().map((question, index) => (
                  <div 
                    key={index} 
                    className="bg-white rounded-lg p-4 shadow-sm border flex items-start"
                  >
                    <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5 mr-2 flex-shrink-0" />
                    <p className="text-gray-700">{question}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Delete Button */}
        <div className="p-4 border-t bg-gray-50">
          <Button variant="destructive" className="w-full" onClick={handleDelete}>
            Delete Meeting
          </Button>
        </div>
      </div>
    </div>
  );
}
