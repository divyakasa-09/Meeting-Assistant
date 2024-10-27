export class TranscriptionService {
    private static BASE_URL = 'http://localhost:8000';
  
    static async transcribeAudio(audioBlob: Blob): Promise<string> {
      const formData = new FormData();
      formData.append('audio_file', audioBlob);
  
      try {
        const response = await fetch(`${this.BASE_URL}/transcribe`, {
          method: 'POST',
          body: formData,
        });
  
        const data = await response.json();
        
        if (!data.success) {
          throw new Error(data.error || 'Transcription failed');
        }
  
        return data.transcript;
      } catch (error) {
        console.error('Transcription error:', error);
        throw error;
      }
    }
  
    static async checkHealth(): Promise<boolean> {
      try {
        const response = await fetch(`${this.BASE_URL}/health`);
        const data = await response.json();
        return data.status === 'healthy';
      } catch (error) {
        return false;
      }
    }
  }