import { useState } from 'react'
import { Plus, Mic, History } from 'lucide-react'
import { Button } from './components/ui/button'
import { MeetingRoom } from './components/MeetingRoom'

function App() {
  const [currentView, setCurrentView] = useState<'home' | 'meeting'>('home')

  if (currentView === 'meeting') {
    return <MeetingRoom onBack={() => setCurrentView('home')} />
  }

  return (
    <div className="max-w-5xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-8">Meeting Assistant</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* New Meeting Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium mb-4">New Meeting</h2>
          <Button 
            className="w-full bg-[#0f172a] hover:bg-[#1e293b] text-white"
            size="lg"
            onClick={() => setCurrentView('meeting')}
          >
            <Plus className="mr-2 h-4 w-4" />
            Start New Meeting
          </Button>
        </div>

        {/* Join Meeting Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium mb-4">Join Meeting</h2>
          <Button 
            variant="outline" 
            className="w-full"
            size="lg"
            onClick={() => setCurrentView('meeting')}
          >
            <Mic className="mr-2 h-4 w-4" />
            Join Existing
          </Button>
        </div>

        {/* History Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium mb-4">History</h2>
          <Button 
            variant="outline" 
            className="w-full"
            size="lg"
          >
            <History className="mr-2 h-4 w-4" />
            View History
          </Button>
        </div>
      </div>
    </div>
  )
}

export default App