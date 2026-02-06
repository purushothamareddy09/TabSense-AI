const BACKEND_URL = "http://localhost:8000/activity";
const SEND_INTERVAL_MS = 5000;

async function sendAllTabs() {
  chrome.tabs.query({}, (tabs) => {
    const data = tabs
      .filter(tab => tab.url.startsWith("http")) // ignore chrome:// tabs
      .map(tab => ({
        tabId: tab.id,
        windowId: tab.windowId,
        title: tab.title,
        url: tab.url,
        switchCount: 0,
        proof: "OPEN_TAB_" + Date.now()
      }));

    fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tabs: data })
    })
    .then(res => res.json())
    .then(resp => console.log("Sent tabs:", resp))
    .catch(err => console.error("Error sending tabs:", err));
  });
}

// Send every 5 seconds
setInterval(sendAllTabs, SEND_INTERVAL_MS);
sendAllTabs(); // initial send