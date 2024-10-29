import { useState } from 'react'
import { Button } from './components/ui/button'
import { MeetingRoom } from './components/MeetingRoom'

function App() {
  const [currentView, setCurrentView] = useState<'home' | 'meeting'>('home')

  if (currentView === 'meeting') {
    return <MeetingRoom onBack={() => setCurrentView('home')} />
  }

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-semibold">Meeting Assistant</h1>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium mb-4">New Meeting</h2>
          <Button 
            className="w-full"
            size="lg"
            onClick={() => setCurrentView('meeting')}
          >
            Start New Meeting
          </Button>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium mb-4">Join Meeting</h2>
          <Button 
            variant="outline" 
            className="w-full"
            size="lg"
            onClick={() => setCurrentView('meeting')}
          >
            Join Existing
          </Button>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium mb-4">History</h2>
          <Button 
            variant="outline" 
            className="w-full"
            size="lg"
          >
            View History
          </Button>
        </div>
      </div>
    </div>
  )
}

export default App