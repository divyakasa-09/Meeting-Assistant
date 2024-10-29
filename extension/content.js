let recorder = null;
let isRecording = false;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'startRecording' && !isRecording) {
    startRecording();
  } else if (message.action === 'stopRecording' && isRecording) {
    stopRecording();
  }
});

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);
    
    const ws = new WebSocket('ws://localhost:8000/ws/' + generateUUID());
    
    recorder.ondataavailable = async (event) => {
      if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
        ws.send(await event.data.arrayBuffer());
      }
    };
    
    recorder.start(1000);
    isRecording = true;
    
    // Notify popup of recording status
    chrome.runtime.sendMessage({
      type: 'recordingStatus',
      recording: true
    });
    
  } catch (error) {
    console.error('Error starting recording:', error);
  }
}

function stopRecording() {
  if (recorder && isRecording) {
    recorder.stop();
    recorder.stream.getTracks().forEach(track => track.stop());
    recorder = null;
    isRecording = false;
    
    // Notify popup of recording status
    chrome.runtime.sendMessage({
      type: 'recordingStatus',
      recording: false
    });
  }
}

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}