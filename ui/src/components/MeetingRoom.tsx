import { useState, useEffect, useRef } from 'react'
import { Button } from './ui/button'
import { Mic, MicOff, Clock } from 'lucide-react'
import { AudioRecorder } from '../services/AudioRecorder'

interface MeetingRoomProps {
  onBack: () => void
}

export function MeetingRoom({ onBack }: MeetingRoomProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [transcripts, setTranscripts] = useState<string[]>([])
  const [duration, setDuration] = useState(0)
  
  const audioRecorder = useRef<AudioRecorder>(new AudioRecorder())
  const transcriptEndRef = useRef<HTMLDivElement>(null)

  // Handle recording timer
  useEffect(() => {
    let interval: NodeJS.Timeout | undefined
    if (isRecording) {
      interval = setInterval(() => {
        setDuration(prev => prev + 1)
      }, 1000)
    }
    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [isRecording])

  // Auto scroll to bottom when new transcripts arrive
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcripts])

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleStartRecording = async () => {
    try {
      await audioRecorder.current.startRecording((text) => {
        setTranscripts(prev => [...prev, text])
      })
      setIsRecording(true)
    } catch (err) {
      console.error('Error starting recording:', err)
      alert('Error accessing microphone. Please ensure microphone permissions are granted.')
    }
  }

  const handleStopRecording = () => {
    audioRecorder.current.stopRecording()
    setIsRecording(false)
  }

  return (
    <div className="max-w-5xl mx-auto p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">Active Meeting</h1>
          <div className="flex items-center mt-2 text-gray-500">
            <Clock className="w-4 h-4 mr-2" />
            <span>{formatDuration(duration)}</span>
          </div>
        </div>
        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={onBack}
          >
            End Meeting
          </Button>
          <Button
            variant={isRecording ? "destructive" : "default"}
            onClick={() => {
              if (isRecording) {
                handleStopRecording()
              } else {
                handleStartRecording()
              }
            }}
          >
            {isRecording ? <MicOff className="mr-2 h-4 w-4" /> : <Mic className="mr-2 h-4 w-4" />}
            {isRecording ? 'Stop Recording' : 'Start Recording'}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Transcript Panel */}
        <div className="md:col-span-2">
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm h-[600px] overflow-y-auto">
            <h2 className="text-lg font-medium mb-4">Live Transcript</h2>
            <div className="space-y-4">
              {transcripts.length > 0 ? (
                transcripts.map((text, index) => (
                  <p key={index} className="text-gray-700">{text}</p>
                ))
              ) : (
                <p className="text-gray-500">
                  {isRecording 
                    ? 'Listening...' 
                    : 'Click "Start Recording" to begin transcription'}
                </p>
              )}
              <div ref={transcriptEndRef} />
            </div>
          </div>
        </div>

        {/* Summary Panel */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-lg font-medium mb-4">Summary</h2>
            <div className="space-y-4">
              <p className="text-gray-500">
                {isRecording 
                  ? 'Summary will be generated during the meeting...' 
                  : 'Start recording to generate summary'}
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-lg font-medium mb-4">Action Items</h2>
            <div className="space-y-4">
              <p className="text-gray-500">
                {isRecording 
                  ? 'Action items will be detected automatically...' 
                  : 'Start recording to detect action items'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}