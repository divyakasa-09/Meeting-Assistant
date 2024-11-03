import { useState } from 'react';
import { Button } from './components/ui/button';
import { MeetingRoom } from './components/MeetingRoom';
import { MeetingHistory } from './components/MeetingHistory';
import { MeetingService, Meeting } from './services/MeetingService';

type View = 'home' | 'meeting' | 'history';

function App() {
  const [currentView, setCurrentView] = useState<View>('home');
  const [currentMeeting, setCurrentMeeting] = useState<Meeting | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartNewMeeting = async () => {
    try {
      setLoading(true);
      setError(null);
      const title = `Meeting ${new Date().toLocaleString()}`;
      const meeting = await MeetingService.createMeeting(title);
      console.log('Created meeting:', meeting);
      setCurrentMeeting(meeting);
      setCurrentView('meeting');
    } catch (error: any) {
      console.error('Failed to create meeting:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to start meeting. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleEndMeeting = async () => {
    if (currentMeeting) {
      try {
        setLoading(true);
        setError(null);
        await MeetingService.endMeeting(currentMeeting.meeting_id);
        console.log('Meeting ended successfully');
      } catch (error: any) {
        console.error('Failed to end meeting:', error);
        const errorMessage = error.response?.data?.detail || 'Failed to end meeting properly. Please try again.';
        setError(errorMessage);
      } finally {
        setLoading(false);
        setCurrentMeeting(null);
        setCurrentView('home');
      }
    } else {
      setCurrentMeeting(null);
      setCurrentView('home');
    }
  };

  const handleDeleteMeeting = async () => {
    if (currentMeeting) {
      try {
        setLoading(true);
        setError(null);
        await MeetingService.deleteMeeting(currentMeeting.meeting_id);
        console.log('Meeting deleted successfully');
        setCurrentMeeting(null);
        setCurrentView('home');
      } catch (error: any) {
        console.error('Failed to delete meeting:', error);
        const errorMessage = error.response?.data?.detail || 'Failed to delete meeting. Please try again.';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleJoinMeeting = async (meeting: Meeting) => {
    try {
      if (!meeting.is_active) {
        setError('This meeting has ended and cannot be joined.');
        return;
      }
      setCurrentMeeting(meeting);
      setCurrentView('meeting');
      setError(null);
    } catch (error: any) {
      console.error('Failed to join meeting:', error);
      setError('Failed to join meeting. Please try again.');
    }
  };

  const handleViewHistory = () => {
    setError(null);
    setCurrentView('history');
  };

  // History View
  if (currentView === 'history') {
    return (
      <MeetingHistory
        onJoinMeeting={handleJoinMeeting}
        onBack={() => {
          setError(null);
          setCurrentView('home');
        }}
      />
    );
  }

  // Meeting View
  if (currentView === 'meeting') {
    if (!currentMeeting) {
      return (
        <div className="max-w-5xl mx-auto p-8">
          <div className="text-center">
            <p className="text-red-500">Error: No meeting data available</p>
            <Button 
              className="mt-4" 
              onClick={() => {
                setError(null);
                setCurrentView('home');
              }}
            >
              Return Home
            </Button>
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-5xl mx-auto p-8">
        <MeetingRoom
          onBack={handleEndMeeting}
          meetingId={currentMeeting.meeting_id}
          meetingTitle={currentMeeting.title}
        />
        {/* Delete Meeting Button */}
        <Button
          className="mt-4 bg-red-500 text-white"
          onClick={handleDeleteMeeting}
          disabled={loading}
        >
          {loading ? 'Deleting...' : 'Delete Meeting'}
        </Button>
      </div>
    );
  }

  // Home View
  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-semibold">Meeting Assistant</h1>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-500 rounded-lg flex justify-between items-center">
          <p>{error}</p>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setError(null)}
          >
            Dismiss
          </Button>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* New Meeting Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:border-blue-200 transition-colors">
          <h2 className="text-lg font-medium mb-4">New Meeting</h2>
          <Button
            className="w-full"
            size="lg"
            onClick={handleStartNewMeeting}
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-white rounded-full border-t-transparent"></div>
                Starting...
              </span>
            ) : (
              'Start New Meeting'
            )}
          </Button>
        </div>

        {/* Join Meeting Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:border-blue-200 transition-colors">
          <h2 className="text-lg font-medium mb-4">Join Meeting</h2>
          <Button
            variant="outline"
            className="w-full"
            size="lg"
            onClick={() => {
              setError(null);
              setCurrentView('history');
            }}
            disabled={loading}
          >
            Join Existing
          </Button>
        </div>

        {/* History Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:border-blue-200 transition-colors">
          <h2 className="text-lg font-medium mb-4">History</h2>
          <Button
            variant="outline"
            className="w-full"
            size="lg"
            onClick={handleViewHistory}
            disabled={loading}
          >
            View History
          </Button>
        </div>
      </div>
    </div>
  );
}

export default App;
