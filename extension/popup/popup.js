document.getElementById('connectBtn').addEventListener('click', () => {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      const currentTab = tabs[0];
      if (currentTab.url.includes('zoom.us')) {
        chrome.tabs.sendMessage(currentTab.id, {action: 'toggleCapture'});
      } else {
        alert('Please open a Zoom meeting first');
      }
    });
  });
  document.getElementById('openApp').addEventListener('click', () => {
    window.open('http://localhost:5173', '_blank');
  });