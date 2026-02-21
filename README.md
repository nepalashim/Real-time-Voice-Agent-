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
│   ├── creds.json    # Your Google Service Account key (DO NOT commit)
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
- Uses a **Google Service Account** – the `creds.json` file is a Service Account key downloaded from Google Cloud Console.
- No browser sign-in required – the Service Account authenticates server-to-server automatically.
- **Important:** Your Google Calendar must be shared with the Service Account email (e.g., `voice-scheduler@project-id.iam.gserviceaccount.com`) so it has permission to create events.
- Also supports OAuth2 Desktop flow as a fallback (see `calendar_utils.py` for details).

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

### Step 1: Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. **Create a new project** — name it something like `Voice-Scheduler-Agent`.
3. **Enable the Google Calendar API** — search for it in the API Library and click Enable.
4. **Create a Service Account:**
   - Navigate to **IAM & Admin → Service Accounts**.
   - Click **+ Create Service Account**.
   - Give it a name (e.g., `voice-scheduler`) and click **Create and Continue**.
   - Assign the role **Owner** or **Editor**, then click **Done**.
5. **Generate a JSON key:**
   - On the Service Accounts page, click the **email address** of the service account you just created.
   - Go to the **Keys** tab.
   - Click **Add Key → Create new key**.
   - Select **JSON** as the key type and click **Create**.
   - A `.json` file will automatically download to your computer.
6. **Rename** the downloaded file to `creds.json` and place it in the `backend/` folder.
7. **Share your Google Calendar with the Service Account:**
   - Open [Google Calendar](https://calendar.google.com).
   - Click the three dots next to your calendar → **Settings and sharing**.
   - Under **Share with specific people**, click **+ Add people**.
   - Paste the Service Account email (e.g., `voice-scheduler@project-id.iam.gserviceaccount.com`).
   - Set permission to **Make changes to events** and click **Send**.

### Step 2: Start ngrok

Since Vapi needs to send requests to your local machine, you need a public URL:

1. [Install ngrok](https://ngrok.com/download) if you haven't already.
2. Run:
   ```bash
   ngrok http 8000
   ```
3. Note the **Forwarding** URL (e.g., `https://xxxx-xxxx.ngrok-free.dev`). You'll need this in the next step.

### Step 3: Configure Vapi Dashboard

1. Log in to [Vapi.ai](https://vapi.ai/) and open the Dashboard.
2. **Create a New Assistant:**
   - **Model Tab:** Select **GPT-4o** as the model and set the **System Prompt** (this is the main engineering prompt — kept confidential by Ashim).
   - **Tools Tab:** Create a new **Function** tool and paste the `book_appointment` schema with these parameters:
     - `name` (string, required) – caller's name
     - `start_time` (string, required) – ISO 8601 datetime
     - `end_time` (string, optional) – ISO 8601 datetime
     - `title` (string, optional) – meeting title
   - Set the **Tool Server URL** to your ngrok URL followed by `/webhook/calendar`:
     ```
     https://xxxx-xxxx.ngrok-free.dev/webhook/calendar
     ```

### Step 4: Start the Backend

```bash
# Terminal 1 – activate the virtual environment
cd /media/ashimnepal/Disk/AGENTS/VoiceaiAgent
source myenv/bin/activate

# Start the FastAPI server
cd backend

uvicorn main:app --host 0.0.0.0 --port 8000 --reload 

or

python main.py
```

The server runs at `http://localhost:8000`.

> **Note:** With Service Account auth, no browser sign-in is needed. The backend authenticates automatically using `creds.json`.

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
| Call button stays on "Connecting…" | Verify your Vapi public key in `frontend/index.html` |
| AI talks but doesn't book | Check that the Server URL in Vapi dashboard points to your ngrok URL + `/webhook/calendar` |
| Backend error: "No valid Google credentials" | Make sure `creds.json` exists in the `backend/` folder and `GOOGLE_SERVICE_ACCOUNT_FILE` is set in `.env` |
| "Insufficient permissions" on Calendar API | Ensure you shared your Google Calendar with the Service Account email and gave it **Make changes to events** permission |
| Token expired (OAuth2 fallback only) | Delete `backend/token.json` and restart – it will re-authenticate |
| ngrok URL changed | Update the Server URL in Vapi dashboard |
| Event not in calendar | Check the `GOOGLE_CALENDAR_ID` in `.env` – use `primary` for your main calendar |

---

## Environment Variables (`backend/.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to Service Account JSON key | `creds.json` |
| `GOOGLE_CALENDAR_ID` | Calendar to create events in (your Gmail address or `primary`) | `yourname@gmail.com` |
| `TIMEZONE` | IANA timezone for events | `Asia/Kathmandu` |

Example `.env`:

```env
# Backend – Voice AI Scheduling Agent
GOOGLE_SERVICE_ACCOUNT_FILE=creds.json
# Set this to your Gmail address (e.g., yourname@gmail.com) after sharing your calendar with the service account
GOOGLE_CALENDAR_ID=yourname@gmail.com
TIMEZONE=Asia/Kathmandu
```

---

## Frontend Config (`frontend/index.html`)

The Vapi widget is configured via an inline `<script>` block in `index.html`:

| Setting | Description |
|---------|-------------|
| `apiKey` | Your Vapi public API key (passed to `vapiSDK.run()`) |
| `assistant` | Your Vapi assistant ID |

`frontend/app.js` handles transcript display only (no config constants).

Vapi-Server-URL when ran locally: https://encinal-allotropically-milissa.ngrok-free.dev/webhook/calendar

---

## New HR Onboarding Guide

If a new HR team member wants to use this Voice AI Scheduling Agent on their own machine, follow these steps:

### 1. Clone the Project

```bash
git clone <repository-url>
cd VoiceaiAgent
```

### 2. Set Up Python Environment

```bash
python3 -m venv myenv
source myenv/bin/activate   # On Windows: myenv\Scripts\activate
pip install -r requirements.txt
```

### 3. Google Cloud Setup

Follow **Step 1** from the Setup & Testing Guide above to:
- Create a Google Cloud project and enable the Calendar API.
- Create a Service Account and download the JSON key as `creds.json`.
- Place `creds.json` in the `backend/` folder.
- Share your Google Calendar with the Service Account email (give **Make changes to events** permission).

### 4. Configure Environment Variables

Create a `backend/.env` file (or copy from `backend/.env.example`):

```env
# Backend – Voice AI Scheduling Agent
GOOGLE_SERVICE_ACCOUNT_FILE=creds.json
# Set this to your Gmail address (e.g., yourname@gmail.com) after sharing your calendar with the service account
GOOGLE_CALENDAR_ID=yourname@gmail.com
TIMEZONE=Asia/Kathmandu
```

Replace `yourname@gmail.com` with your actual Gmail address.

### 5. Configure Vapi.ai

1. Go to [Vapi.ai](https://vapi.ai/) and create an account (or get access from your team).
2. **Create a New Assistant:**
   - **Model Tab:** Select **GPT-4o** and set the System Prompt (get this from Ashim).
   - **Tools Tab:** Create a new **Function** tool.
     - Paste the `book_appointment` schema (get this from the existing assistant config or from Ashim).
     - Set the **Server URL** to your ngrok URL + `/webhook/calendar` (see next step).
3. Note down your **Vapi Public Key** and **Assistant ID** from the dashboard.
4. Update `frontend/index.html` with your own Vapi Public Key and Assistant ID (in the inline `<script>` block).

### 6. Configure ngrok

1. [Download and install ngrok](https://ngrok.com/download).
2. Sign up at [ngrok.com](https://ngrok.com) and authenticate:
   ```bash
   ngrok config add-authtoken <your-ngrok-auth-token>
   ```
3. Start your FastAPI backend:
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. In a separate terminal, expose it via ngrok:
   ```bash
   ngrok http 8000
   ```
5. Copy the `https://...` **Forwarding URL** from ngrok output.
6. Go back to the **Vapi Dashboard** → your assistant's Tool settings → paste the ngrok URL followed by `/webhook/calendar` as the Server URL.

> **Note:** The free ngrok URL changes every time you restart ngrok. Update the Vapi Tool URL each time, or use a paid ngrok plan for a stable domain.

### 7. Run & Test

1. Make sure the backend is running (`uvicorn main:app ...`).
2. Make sure ngrok is running and the URL is set in Vapi.
3. Open the frontend:
   ```bash
   cd frontend
   python -m http.server 5500
   # Open http://localhost:5500 in your browser
   ```
4. Click **"Call Assistant"**, allow microphone access, and test the full conversation flow.
5. Verify the event appears on your [Google Calendar](https://calendar.google.com).


### Backend was deployed on Render on a free tier cause it to be slow and problematic so it's better to Clone the project and run Locally as instruction  given above, Still the Frontend just UI is deployed in Vercel as shown below: 

## Live Demo

| Resource | Link |
|----------|------|
| **Live Frontend App** | [VoiceAssistant](https://voiceai-agent.vercel.app/) |
| **Demo Video** | [Watch on Google Drive](https://drive.google.com/drive/folders/1ejIPous6BVLb7IBsEUAB5pnHXOQ9Yi82?usp=sharing) |