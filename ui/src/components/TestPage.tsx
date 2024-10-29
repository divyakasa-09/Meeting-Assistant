import { useState, useEffect } from 'react'
import { Button } from './ui/button'

export function TestPage() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [audioStatus, setAudioStatus] = useState<'untested' | 'available' | 'unavailable'>('untested')
  
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'))
  }, [])

  const testAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())
      setAudioStatus('available')
    } catch (err) {
      setAudioStatus('unavailable')
      console.error('Audio error:', err)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-8">System Test</h1>
      
      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-semibold mb-2">Backend Status</h2>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              backendStatus === 'online' ? 'bg-green-500' : 
              backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
            }`} />
            <span className="capitalize">{backendStatus}</span>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-2">Audio System</h2>
          <div className="flex items-center gap-4">
            <Button onClick={testAudio}>
              Test Microphone
            </Button>
            <span className="capitalize">{audioStatus}</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h2 className="text-lg font-semibold mb-2">System Requirements</h2>
          <ul className="space-y-2">
            <li>✓ Chrome browser</li>
            <li>✓ Microphone access</li>
            <li>✓ Backend server running</li>
            <li>✓ WebSocket support</li>
          </ul>
        </div>
      </div>
    </div>
  )
}