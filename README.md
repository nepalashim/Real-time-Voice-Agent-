# Voice AI Scheduling Agent

A real-time voice assistant that books appointments on your Google Calendar through a natural conversation. You speak, the AI collects your name, preferred date/time, and meeting title, then creates the event automatically.

---

## Project Structure

```
VoiceaiAgent/
├── frontend/
│   ├── index.html          # UI – open in browser, no build needed
│   ├── style.css           # Dark glassmorphism styling
│   └── app.js              # Vapi SDK integration (vanilla JS)
├── backend/
│   ├── main.py             # FastAPI server – receives tool calls from Vapi
│   ├── calendar_utils.py   # Google Calendar auth & event creation
│   ├── creds.json          # Your Google OAuth2 credentials (DO NOT commit)
│   └── .env                # Environment config
├── requirements.txt        # Python dependencies
├── myenv/                  # Python virtual environment
└── README.md               # ← You are here
```

---

## How It All Works

### Conversation Flow

```
User clicks "Call Assistant"
        │
        ▼
Vapi connects a voice call (browser microphone)
        │
        ▼
AI Assistant (hosted by Vapi) starts talking:
   1. "Hi! What's your name?"
   2. "When would you like to schedule?"
   3. "Any specific meeting title?"
   4. "Let me confirm: [details]. Shall I book it?"
   5. User confirms → AI triggers `book_appointment` tool call
        │
        ▼
Vapi sends a webhook POST to your backend (via ngrok)
   URL: https://<your-ngrok>.ngrok-free.dev/webhook/calendar
        │
        ▼
FastAPI backend receives the tool call:
   → Extracts name, start_time, end_time, title
   → Calls Google Calendar API to insert event
   → Returns success message to Vapi
        │
        ▼
AI reads the result back to you:
   "Your appointment has been booked!"
```

### Google Calendar Integration Explained

**Authentication** (`calendar_utils.py`):
- Uses **OAuth2 Desktop flow** – your `creds.json` file is the OAuth2 client secret downloaded from Google Cloud Console.
- On first run, a browser window opens asking you to sign in and grant Calendar access.
- After consent, a `token.json` is saved so you won't be prompted again.
- The token auto-refreshes when it expires.

**Event Creation** (`calendar_utils.py → create_event()`):
- Receives: `name`, `start_time` (ISO 8601), optional `end_time`, optional `title`
- If no `end_time` → defaults to 30 minutes after start
- If no `title` → defaults to "Meeting with {name}"
- Inserts the event into your Google Calendar using the Calendar API v3
- Returns the created event object (includes a clickable Google Calendar link)

**Webhook Endpoint** (`main.py → /webhook/calendar`):
- Vapi sends a JSON payload containing the tool call details
- The endpoint extracts the function arguments and calls `create_event()`
- Returns a result string that the AI reads aloud to the caller

---

## Setup & Testing Guide

### Prerequisites

- Python 3.12 (already in `myenv`)
- A Google Cloud project with Calendar API enabled
- A Vapi account with an assistant configured
- ngrok for exposing your local backend

### Step 1: Google Cloud Setup (already done)

You've already downloaded `creds.json`. For reference, here's what was needed:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google Calendar API**
3. Go to **Credentials** → Create **OAuth 2.0 Client ID** (Desktop app)
4. Download the JSON → save as `backend/creds.json`

### Step 2: Start ngrok (already done)

```bash
ngrok http 8000
```

Note your forwarding URL (e.g. `https://encinal-allotropically-milissa.ngrok-free.dev`).

### Step 3: Configure Vapi Dashboard

1. Log in to [Vapi Dashboard](https://dashboard.vapi.ai/)
2. Open your assistant (ID: `40f8d85e-98db-4fd0-890e-83b2bb3d383e`)
3. Set the **Server URL** to:
   ```
   https://encinal-allotropically-milissa.ngrok-free.dev/webhook/calendar
   ```
4. Make sure the assistant has a `book_appointment` tool/function defined with these parameters:
   - `name` (string, required) – caller's name
   - `start_time` (string, required) – ISO 8601 datetime
   - `end_time` (string, optional) – ISO 8601 datetime
   - `title` (string, optional) – meeting title

### Step 4: Start the Backend

```bash
# Terminal 1 – activate the virtual environment
cd /media/ashimnepal/Disk/VoiceaiAgent
source myenv/bin/activate

# Start the FastAPI server
cd backend

uvicorn main:app --host 0.0.0.0 --port 8000 --reload 

or

python main.py
```

The server runs at `http://localhost:8000`.

**First-time Google auth:** A browser window will open asking you to sign in with your Google account and allow Calendar access. This happens only once – after that, `token.json` is saved.

### Step 5: Verify Backend is Running

```bash
# In another terminal, test the health endpoint:
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok"}
```

### Step 6: Open the Frontend

Simply open the file in your browser:

```bash
# Option A: direct file open
xdg-open frontend/index.html

# Option B( I RECOMMEND): use Python's built-in server (better for some browsers)
cd frontend
python -m http.server 5500
# Then open http://localhost:5500
```

### Step 7: Test the Voice Agent

1. **Click "Call Assistant"** – the button turns yellow (connecting)
2. **Allow microphone access** when the browser prompts
3. **The AI will greet you** – listen and respond:


   - It asks for your **name** → say your name
   - It asks for **date and time** → say something like "Tomorrow at 2 PM"
   - It asks for a **meeting title** (optional) → say a title or "no title"
   - It **confirms the details** → say "Yes, book it"
4. **The AI triggers `book_appointment`** → your backend receives the webhook
5. **Check your terminal** – you'll see logs like:
   ```
   INFO: Received webhook payload: {...}
   INFO: Event created: https://www.google.com/calendar/event?eid=...
   ```
6. **The AI confirms** – "Your appointment has been booked!"
7. **Check Google Calendar** – open [calendar.google.com](https://calendar.google.com) and see the new event

### Step 8: Verify the Calendar Event

Go to [Google Calendar](https://calendar.google.com) and look for:
- **Title**: Whatever you said (or "Meeting with {your name}")
- **Time**: The date/time you requested
- **Duration**: 30 minutes (default)
- **Description**: "Scheduled by Voice AI Agent for {your name}"

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Vapi SDK not loaded" in console | Check internet connection – the SDK loads from CDN |
| Call button stays on "Connecting…" | Verify your Vapi public key in `frontend/app.js` |
| AI talks but doesn't book | Check that the Server URL in Vapi dashboard points to your ngrok URL + `/webhook/calendar` |
| Backend error: "No valid Google credentials" | Make sure `creds.json` exists in the `backend/` folder |
| Google auth browser window doesn't open | Run `python main.py` directly (not via uvicorn) for the first auth |
| Token expired | Delete `backend/token.json` and restart – it will re-authenticate |
| ngrok URL changed | Update the Server URL in Vapi dashboard AND in `frontend/app.js` |
| Event not in calendar | Check the `GOOGLE_CALENDAR_ID` in `.env` – use `primary` for your main calendar |

---

## Environment Variables (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CREDENTIALS_FILE` | Path to OAuth2 client secret JSON | – |
| `GOOGLE_TOKEN_FILE` | Path to cached auth token | `token.json` |
| `GOOGLE_CALENDAR_ID` | Calendar to create events in | `primary` |
| `TIMEZONE` | IANA timezone for events | `Asia/Kathmandu` |

---

## Frontend Config (`frontend/app.js`)

| Constant | Description |
|----------|-------------|
| `VAPI_PUBLIC_KEY` | Your Vapi public API key |
| `VAPI_ASSISTANT_ID` | Your Vapi assistant ID |
| `BACKEND_URL` | ngrok URL + `/webhook/calendar` (used as fallback if not set in Vapi dashboard) |
