"""
FastAPI backend for the Voice AI Scheduling Agent.

Endpoints
---------
POST /webhook/calendar
    Receives ALL Vapi server messages. Returns 200 for informational events.
    Processes tool-calls (book_appointment) and returns results.

GET /health
    Simple liveness check.
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from calendar_utils import create_event

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("webhook.log"),
    ],
)
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(title="Voice AI Scheduling Agent – Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/calendar")
async def webhook_calendar(request: Request):
    """
    Handle ALL Vapi server URL messages.

    Vapi sends many event types to the server URL:
      - status-update, transcript, end-of-call-report, etc. (informational → return 200)
      - tool-calls (requires a response with results)

    Tool-calls payload format (from Vapi docs):
    {
      "message": {
        "type": "tool-calls",
        "toolCallList": [
          {
            "id": "abc123",
            "name": "book_appointment",
            "parameters": { "name": "Ashim", "start_time": "..." }
          }
        ]
      }
    }

    Expected response:
    {
      "results": [
        { "name": "book_appointment", "toolCallId": "abc123", "result": "..." }
      ]
    }
    """
    body = await request.json()

    # ── Full payload logging for debugging ───────────────────────────
    import json
    logger.info("RAW PAYLOAD: %s", json.dumps(body, indent=2, default=str)[:3000])

    message = body.get("message", {})
    msg_type = message.get("type", "unknown")

    logger.info("Received Vapi event: %s", msg_type)

    # ── Only process tool-calls; acknowledge everything else ─────────
    if msg_type != "tool-calls":
        logger.info("Ignoring event type: %s", msg_type)
        return JSONResponse(content={}, status_code=200)

    # ── Handle tool-calls ────────────────────────────────────────────
    tool_calls = message.get("toolCallList", [])
    logger.info("Tool calls received: %s", tool_calls)

    results = []

    for tc in tool_calls:
        tc_id    = tc.get("id", "")
        tc_name  = tc.get("name", "")
        # Vapi sends "arguments" in toolCallList (docs confirmed)
        params   = tc.get("arguments", tc.get("parameters", {}))

        # Also handle legacy format (function.name / function.arguments)
        if not tc_name:
            func = tc.get("function", {})
            tc_name = func.get("name", "")
            params = func.get("arguments", func.get("parameters", params))

        logger.info("Processing tool: %s with params: %s", tc_name, params)

        if tc_name == "book_appointment":
            try:
                event = create_event(
                    name=params.get("name", "Unknown"),
                    start_time=params.get("start_time"),
                    end_time=params.get("end_time"),
                    title=params.get("title"),
                )
                result_text = (
                    f"Appointment booked successfully! "
                    f"Event: {event.get('summary')} on "
                    f"{event['start']['dateTime']}. "
                    f"Calendar link: {event.get('htmlLink')}"
                )
                logger.info("Event created: %s", event.get("htmlLink"))
            except Exception as exc:
                logger.error("Failed to create event: %s", traceback.format_exc())
                result_text = f"Sorry, I couldn't book the appointment. Error: {exc}"

            results.append({
                "name": tc_name,
                "toolCallId": tc_id,
                "result": result_text,
            })
        else:
            results.append({
                "name": tc_name,
                "toolCallId": tc_id,
                "result": f"Unknown tool: {tc_name}",
            })

    return {"results": results}


# ── Entrypoint ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
