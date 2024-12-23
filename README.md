# Meeting Assistant AI

## Overview
Meeting Assistant AI is a real-time meeting transcription and analysis application. It captures live audio from the microphone and system, transcribes it using Google Speech-to-Text, and generates actionable insights such as meeting summaries, follow-up questions, and action items. The application provides a seamless interface for managing live transcripts and insights during a meeting. It is designed to be used during Zoom, Google Meet, and Microsoft Teams meetings when users join via a browser, allowing seamless integration with virtual meeting platforms.

---

## Features
### Real-Time Capabilities
- **Live Dual Audio Input Handling**: Processes audio from both the system and microphone.
- **Real-Time Transcription**: Displays live transcripts of ongoing discussions.
- **Progressive Insights**: Continuously generates meeting summaries, action items, and follow-up questions.

### AI-Driven Insights
- **Summaries**: Generates concise meeting summaries with key topics and decisions.
- **Follow-Up Questions**: Suggests insightful questions based on the discussion.
- **Action Items**: Extracts actionable tasks from meeting transcripts.

### User Interface
- **Frontend**: React-based interface displaying live transcripts, insights, and action items.
- **Interactive Controls**: Start/stop recording, view live updates, and manage meeting details.

### Virtual Meeting Integration
- **Browser-Based Usage**: Captures audio and video streams directly from Zoom, Google Meet, or Microsoft Teams when accessed via a browser.
- **Platform-Specific APIs**: Integrates with Zoom SDK, Microsoft Graph API (Teams), and Google Meet's browser features to fetch meeting metadata and support automated recording.
- **Audio and Video Context**: Processes both audio and video streams for enhanced meeting insights, such as speaker activity detection and video-based interaction analysis.

---

## Technologies Used
### Backend
- **Framework**: FastAPI
  - Enables asynchronous programming for handling WebSocket connections and REST API endpoints.
  - Provides robust dependency injection for database session management.
- **Real-Time Communication**: WebSocket
  - Supports bi-directional communication for streaming audio data in real-time.
- **Speech-to-Text**: Google Speech-to-Text API
  - Handles transcription of audio data with enhanced models for punctuation and word confidence.
- **AI**: OpenAI GPT Models
  - Generates progressive and final summaries, follow-up questions, and action items.
- **Database**: PostgreSQL
  - Relational database used to store meeting, transcript, summary, and action item data.
- **ORM**: SQLAlchemy
  - Defines database models and relationships, ensuring efficient queries and scalability.
- **Audio Processing**:
  - **NumPy**: Processes raw audio data for silence detection and noise filtering.
  - **Google Speech Client**: Streams audio data for transcription.

### Frontend
- **Framework**: React
  - Provides a responsive, real-time UI for displaying transcripts, summaries, and action items.
- **UI Libraries**: Material UI, Tailwind CSS
  - Enables modern and consistent user interface designs.
- **State Management**: React Hooks, Context API
  - Manages application state for real-time updates and user interactions.

### Additional Tools
- **Task Scheduling**: Asyncio
  - Handles periodic tasks like generating progressive summaries during meetings.
- **Deployment**: Uvicorn
  - Serves the FastAPI application for development and production environments.
- **Testing and Debugging**:
  - **Logging**: Captures detailed logs for debugging and monitoring.
  - **Retry Mechanisms**: Ensures resilience during OpenAI API or WebSocket failures.

---

## Setup Instructions

### Prerequisites
1. **Python**: Version 3.9+
2. **Node.js**: Version 16+
3. **Google Cloud Account**: For Speech-to-Text API
4. **OpenAI API Key**: For generating insights

### Backend Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Meeting-Assistant
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv env
   source env/bin/activate  # For Linux/Mac
   env\Scripts\activate   # For Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="<your_openai_api_key>"
   export GOOGLE_APPLICATION_CREDENTIALS="<path_to_google_credentials_json>"
   export DATABASE_URL="postgresql+psycopg2://<username>:<password>@<host>/<db_name>"
   ```

5. Initialize the database:
   ```bash
   alembic upgrade head
   ```

6. Start the backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Access the application at [http://localhost:5173](http://localhost:5173).

---

## How It Works

### Architecture
1. **Audio Processing**:
   - Captures live audio streams from the microphone and system.
   - Filters silent and noisy chunks using NumPy.
   - Streams audio to Google Speech-to-Text API for transcription.

2. **AI Integration**:
   - Processes transcripts using OpenAI GPT models to generate summaries, action items, and follow-up questions.

3. **Data Management**:
   - Stores meetings, transcripts, and insights in PostgreSQL.
   - Manages relational data using SQLAlchemy ORM.

4. **Frontend**:
   - Displays live transcripts and insights.
   - Allows users to manage meetings interactively.

5. **Browser-Based Meeting Integration**:
   - Hooks into browser WebRTC streams to capture audio and video during Zoom, Google Meet, and Teams meetings.
   - Uses APIs specific to each platform to fetch metadata, attendee lists, and automate meeting start/stop actions.

### Key Components
- **Backend**:
  - `EnhancedAudioProcessor`: Handles live audio processing.
  - `EnhancedAIService`: Communicates with OpenAI API to generate insights.
  - `StreamManager`: Manages audio streams and buffers.
  - **WebSocket Endpoint**:
    - Streams live audio from the client to the server.
    - Sends real-time transcripts and insights back to the client.

- **Frontend**:
  - `MeetingRoom`: Displays live transcripts, summaries, and action items.
  - `AudioRecorder`: Captures and streams audio to the backend.
  - **Progressive Insights**:
    - Updates summaries and action items every 30 seconds during active meetings.

---

## API Endpoints

### WebSocket
- **`/ws/{client_id}`**: Establishes a WebSocket connection for live audio streaming.

### REST Endpoints
- **Meetings**:
  - `POST /meetings/`: Create a new meeting.
  - `GET /meetings/`: List all meetings.
  - `GET /meetings/{meeting_id}/details`: Get meeting details with transcripts and action items.
  - `PUT /meetings/{meeting_id}/end`: End a meeting.
  - `DELETE /meetings/{meeting_id}`: Delete a meeting.

- **Insights**:
  - `POST /meetings/{meeting_id}/live-insights`: Generate live insights.
  - `POST /meetings/{meeting_id}/generate-summary`: Generate a final meeting summary.

---

## Future Enhancements
- **Multilingual Support**: Add transcription and analysis for additional languages.
- **Cloud Deployment**: Deploy the application on AWS/GCP with CI/CD pipelines.
- **Mobile Integration**: Extend the interface for mobile platforms.
- **Enhanced Security**: Implement OAuth for user authentication and permissions.


---

## Contact
For questions or feedback, contact Divya Kasa at [divyakasa.edu@gmail.com]

