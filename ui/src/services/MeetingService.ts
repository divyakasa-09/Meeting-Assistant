import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface Meeting {
  id: number;
  meeting_id: string;
  title: string;
  start_time: string;
  end_time: string | null;
  is_active: boolean;
  transcripts: Array<{
    id: number;
    text: string;
    timestamp: string;
    speaker?: string;
  }>;
  action_items: Array<{
    id: number;
    description: string;
    assigned_to?: string;
    due_date?: string;
    status: string;
  }>;
}

export class MeetingService {
  static async createMeeting(title?: string): Promise<Meeting> {
    try {
      const response = await axios.post(`${API_BASE_URL}/meetings/`, {
        title: title || `Meeting ${new Date().toLocaleString()}`
      });
      return response.data;
    } catch (error: any) {
      console.error('Error creating meeting:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create meeting');
    }
  }

  static async getMeetings(): Promise<Meeting[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/meetings/`);
      return response.data;
    } catch (error: any) {
      console.error('Error getting meetings:', error);
      throw new Error(error.response?.data?.detail || 'Failed to load meetings');
    }
  }

  static async getMeeting(meeting_id: string): Promise<Meeting> {
    try {
      console.log('Fetching meeting details for:', meeting_id);
      const response = await axios.get(`${API_BASE_URL}/meetings/${meeting_id}/details`);
      console.log('Meeting details response:', response.data);
      
      // Verify transcripts are present
      if (response.data.transcripts) {
        console.log('Number of transcripts:', response.data.transcripts.length);
      } else {
        console.warn('No transcripts array in response');
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error getting meeting details:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
      }
      throw new Error(error.response?.data?.detail || 'Failed to load meeting details');
    }
  }
  static async deleteMeeting(meetingId: string): Promise<void> {
    try {
        await axios.delete(`${API_BASE_URL}/meetings/${meetingId}`);
        console.log('Meeting deleted successfully');
    } catch (error: any) {
        console.error('Error deleting meeting:', error);
        if (error.response) {
            console.error('Error status:', error.response.status);
            console.error('Error data:', error.response.data);
        }
        throw new Error(error.response?.data?.detail || 'Failed to delete meeting');
    }
}

  static async endMeeting(meetingId: string): Promise<void> {
    try {
      const response = await axios.put(`${API_BASE_URL}/meetings/${meetingId}/end`, {}, {
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      });
      
      if (response.status !== 200) {
        throw new Error(response.data.detail || 'Failed to end meeting');
      }

      console.log('Meeting ended successfully:', response.data);
    } catch (error: any) {
      console.error('Error ending meeting:', error);
      throw new Error(error.response?.data?.detail || 'Failed to end meeting');
    }
  }
}
