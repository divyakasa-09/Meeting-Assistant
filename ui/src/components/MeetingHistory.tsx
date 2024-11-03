import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { MeetingService, Meeting } from '../services/MeetingService';
import { MeetingDetails } from './MeetingDetails';
import { RefreshCw, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface MeetingHistoryProps {
  onJoinMeeting: (meeting: Meeting) => void;
  onBack: () => void;
}

export function MeetingHistory({ onJoinMeeting, onBack }: MeetingHistoryProps) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await MeetingService.getMeetings();
      setMeetings(data);
    } catch (err) {
      setError('Failed to load meetings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMeetings();
  }, []);

  const handleDeleteMeeting = async (meetingId: string) => {
    try {
      await MeetingService.deleteMeeting(meetingId);
      setMeetings((prev) => prev.filter((meeting) => meeting.meeting_id !== meetingId));
      setIsDetailsOpen(false);
      setSelectedMeeting(null);
    } catch (error: any) {
      setError(error.message || 'Failed to delete meeting. Please try again.');
    }
  };

  const handleViewDetails = (meeting: Meeting) => {
    setSelectedMeeting(meeting);
    setIsDetailsOpen(true);
  };

  const handleRefresh = () => {
    loadMeetings();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex h-screen">
        <div className="flex-1 p-8">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-2xl font-semibold">Meeting History</h1>
            <Button variant="outline" onClick={onBack}>Back</Button>
          </div>
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="text-gray-500">Loading meetings...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <div className={`flex-1 p-8 transition-all duration-300 ${isDetailsOpen ? 'pr-[40%]' : ''}`}>
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-semibold">Meeting History</h1>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={onBack}>
              Back
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 text-red-500 rounded-lg flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p>{error}</p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-red-600 hover:text-red-700"
                onClick={() => setError(null)}
              >
                Dismiss
              </Button>
            </div>
          </div>
        )}

        {meetings.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="flex flex-col items-center space-y-3">
              <Clock className="h-12 w-12 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900">No Meetings Found</h3>
              <p className="text-gray-500">Start a new meeting to begin recording.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4 overflow-y-auto pr-2" style={{ maxHeight: 'calc(100vh - 8rem)' }}>
            {meetings.map((meeting) => (
              <div
                key={meeting.id}
                className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:border-blue-200 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-2">
                    <h2 className="text-lg font-medium">{meeting.title}</h2>
                    <div className="space-y-1">
                      <div className="flex items-center text-sm text-gray-500">
                        <Clock className="h-4 w-4 mr-2" />
                        Started: {formatDate(meeting.start_time)}
                      </div>
                      {meeting.end_time && (
                        <div className="flex items-center text-sm text-gray-500">
                          <Clock className="h-4 w-4 mr-2" />
                          Ended: {formatDate(meeting.end_time)}
                        </div>
                      )}
                      <div className="flex items-center">
                        {meeting.is_active ? (
                          <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 mr-2 text-gray-500" />
                        )}
                        <span className={`text-sm px-2 py-1 rounded-full ${getStatusColor(meeting.is_active)}`}>
                          {meeting.is_active ? 'Active' : 'Ended'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {meeting.is_active && (
                      <Button
                        onClick={() => onJoinMeeting(meeting)}
                      >
                        Join Meeting
                      </Button>
                    )}
                    <Button 
                      variant="outline"
                      onClick={() => handleViewDetails(meeting)}
                    >
                      View Details
                    </Button>
                    <Button 
                      variant="outline"  // Now styled the same as "View Details"
                      onClick={() => handleDeleteMeeting(meeting.meeting_id)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>

                {/* Preview Section */}
                {meeting.transcripts && meeting.transcripts.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-sm text-gray-500 mb-2">Latest transcript:</p>
                    <p className="text-sm text-gray-700">
                      {meeting.transcripts[meeting.transcripts.length - 1].text}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedMeeting && (
        <MeetingDetails
          meeting={selectedMeeting}
          isOpen={isDetailsOpen}
          onClose={() => {
            setIsDetailsOpen(false);
            setSelectedMeeting(null);
          }}
          onDelete={handleDeleteMeeting}
        />
      )}
    </div>
  );
}
