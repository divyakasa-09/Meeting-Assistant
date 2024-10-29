chrome.runtime.onInstalled.addListener(() => {
    console.log('Meeting Assistant Extension installed');
  });
  
  // Handle messages from content script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'recordingStatus') {
      // Update extension icon
      chrome.action.setIcon({
        path: {
          16: message.recording ? "icons/icon16-active.png" : "icons/icon16.png"
        }
      });
    }
  });