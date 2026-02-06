from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import requests

# -----------------------------
# App setup
# -----------------------------
app = FastAPI(title="Browser Activity Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# -----------------------------
# Data models
# -----------------------------
class SemanticContent(BaseModel):
    headings: List[str] = []
    text: str = ""

class TabActivity(BaseModel):
    tabId: int
    windowId: int
    title: str
    url: str
    totalActiveMs: int
    switchCount: int
    proof: Optional[str] = None
    semantic: Optional[SemanticContent] = None
    lastUpdated: datetime

class PromptRequest(BaseModel):
    prompt: str

# -----------------------------
# In-memory store
# -----------------------------
TAB_ACTIVITY: Dict[int, TabActivity] = {}

# -----------------------------
# LLaMA helper
# -----------------------------
def call_llama(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return response.json().get("response", "")
    except Exception as e:
        return f"LLaMA call failed: {e}"

# -----------------------------
# API: receive active browser tabs
# -----------------------------
@app.post("/activity")
def receive_activity(payload: dict):
    """
    Receives current active tabs from browser extension.
    Overwrites previous data — keeps only active tabs.
    """
    print("\n===== RAW ACTIVE TABS PAYLOAD =====")
    print(payload)
    print("================================\n")

    now = datetime.utcnow()

    # Clear previous tabs, store only latest active ones
    TAB_ACTIVITY.clear()

    for tab in payload.get("tabs", []):
        TAB_ACTIVITY[tab["tabId"]] = TabActivity(
            tabId=tab["tabId"],
            windowId=tab["windowId"],
            title=tab["title"],
            url=tab["url"],
            totalActiveMs=tab.get("totalActiveMs", 0),
            switchCount=tab.get("switchCount", 0),
            proof=tab.get("proof"),
            semantic=tab.get("semantic"),
            lastUpdated=now
        )

    return {"status": "ok", "active_tabs_count": len(TAB_ACTIVITY)}

# -----------------------------
# Get currently active tabs
# -----------------------------
@app.get("/activity")
def get_activity():
    return {
        "active_tab_count": len(TAB_ACTIVITY),
        "tabs": [tab.dict() for tab in TAB_ACTIVITY.values()]
    }

# -----------------------------
# Analyze all tabs via LLaMA
# -----------------------------
@app.post("/analyze")
def analyze_tabs():
    if not TAB_ACTIVITY:
        return {"error": "No active browser data received"}

    prompt = "You are an AI. Explain the user's activity based ONLY on these tabs:\n\n"
    for tab in TAB_ACTIVITY.values():
        prompt += f"""
Title: {tab.title}
URL: {tab.url}
Active Time (seconds): {tab.totalActiveMs // 1000}
Switch Count: {tab.switchCount}
Proof: {tab.proof}
"""

    print("\n===== PROMPT SENT TO LLaMA =====")
    print(prompt)
    print("================================\n")

    response = call_llama(prompt)
    return {"llama_response": response}

# -----------------------------
# Manual chat endpoint
# -----------------------------
@app.post("/chat")
def chat_with_llm(req: PromptRequest):
    response = call_llama(req.prompt)
    return {"response": response}

# -----------------------------
# What am I doing endpoint
# -----------------------------

@app.get("/what-am-i-doing")
def what_am_i_doing():
    if not TAB_ACTIVITY:
        return {"answer": "No browser tabs are currently open."}

    prompt = "You are an AI assistant. The user has the following browser tabs open. Summarize what the user might be doing based on these tabs:\n\n"

    for i, tab in enumerate(TAB_ACTIVITY.values(), start=1):
        prompt += f"Tab {i}: {tab.title}\n"

    print("\n===== PROMPT SENT TO LLaMA =====")
    print(prompt)
    print("================================\n")

    response = call_llama(prompt)
    return {"answer": response}

# -----------------------------
# Simple UI page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Browser Activity AI</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Roboto', sans-serif;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 40px 20px;
      color: #fff;
      background: #111216;
      background-image: linear-gradient(135deg, #232526 0%, #0f2027 100%);
      position: relative;
    }
    body::before {
      content: "";
      position: absolute;
      top:0; left:0;
      width:100%; height:100%;
      background: rgba(0,0,0,0.7);
      z-index: 0;
    }
    h1 {
      font-size: 3em;
      text-align: center;
      margin-bottom: 20px;
      text-shadow: 3px 3px 10px rgba(0,0,0,0.7);
      color: #ffefc4;
      position: relative;
      z-index: 1;
    }
    .container {
      position: relative;
      z-index: 1;
      background: rgba(30,30,40,0.85);
      backdrop-filter: blur(20px);
      border-radius: 25px;
      padding: 35px 45px;
      width: 100%;
      max-width: 950px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.35);
      display: flex;
      flex-direction: column;
      gap: 25px;
      color: #fff;
    }
    label {
      font-weight: 500;
      margin-bottom: 5px;
      display: block;
    }
    textarea {
      width: 100%;
      border-radius: 15px;
      border: 1px solid #222;
      padding: 15px;
      font-size: 1em;
      resize: vertical;
      color: #fff;
      background: #18191c;
      transition: border 0.3s ease, box-shadow 0.3s ease;
    }
    textarea:focus {
      border-color: #ff9a3c;
      box-shadow: 0 0 15px rgba(255,154,60,0.4);
      outline: none;
    }
    .buttons {
      display: flex;
      gap: 20px;
      margin-top: 10px;
    }
    button {
      flex: 1;
      padding: 16px;
      font-size: 1em;
      border: none;
      border-radius: 15px;
      cursor: pointer;
      font-weight: 700;
      transition: all 0.3s ease;
      box-shadow: 0 8px 25px rgba(0,0,0,0.25);
    }
    button#chatBtn {
      background: linear-gradient(90deg, #ff6ec4, #7873f5);
      color: #fff;
    }
    button#chatBtn:hover {
      background: linear-gradient(90deg, #ff4aad, #5f5ce6);
    }
    button#activityBtn {
      background: linear-gradient(90deg, #43e97b, #38f9d7);
      color: #000;
    }
    button#activityBtn:hover {
      background: linear-gradient(90deg, #3cd473, #2fdad0);
    }
    pre {
      background: rgba(0,0,0,0.7);
      border-radius: 15px;
      padding: 25px;
      max-height: 450px;
      overflow-y: auto;
      font-size: 1em;
      line-height: 1.5;
      white-space: pre-wrap;
      word-wrap: break-word;
      border: 1px solid rgba(255,255,255,0.1);
      color: #fff;
    }
    @media (max-width: 600px) {
      h1 { font-size: 2.2em; }
      .container { padding: 25px 20px; }
      button { padding: 12px; font-size: 0.95em; }
    }
  </style>
</head>
<body>
  <div style="width:100%; max-width:950px; position: relative; z-index: 1;">
    <h1>TabSense AI with LLaMA</h1>
    <div class="container">
      <label for="prompt">Chat with LLaMA:</label>
      <textarea id="prompt" rows="4" placeholder="Type your message here..."></textarea>
      <div class="buttons">
        <button id="chatBtn" onclick="sendChat()">General Ask</button>
        <button id="activityBtn" onclick="askActivity()">What am I doing on browser?</button>
      </div>
      <label for="output">Output:</label>
      <pre id="output">Your AI summary will appear here...</pre>
    </div>
  </div>
  <script>
    async function sendChat() {
      const prompt = document.getElementById("prompt").value;
      if (!prompt.trim()) return;
      document.getElementById("output").innerText = "Thinking...";
      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({prompt})
        });
        const data = await res.json();
        document.getElementById("output").innerText = data.response;
      } catch(e) {
        document.getElementById("output").innerText = "Error: " + e.message;
      }
    }
    async function askActivity() {
      document.getElementById("output").innerText = "Analyzing open tabs...";
      try {
        const res = await fetch("/what-am-i-doing");
        const data = await res.json();
        document.getElementById("output").innerText = data.answer;
      } catch(e) {
        document.getElementById("output").innerText = "Error: " + e.message;
      }
    }
  </script>
</body>
</html>
"""