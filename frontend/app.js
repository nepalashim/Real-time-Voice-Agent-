// ─────────────────────────────────────────────────────────
//  Voice AI Scheduling Agent – Transcript display
//  (Calling is handled by the official Vapi widget)
// ─────────────────────────────────────────────────────────

const statusEl       = document.getElementById("status");
const transcriptBox  = document.getElementById("transcript-box");
const transcriptList = document.getElementById("transcript-list");

function initTranscript(vapi) {
  vapi.on("call-start", () => {
    statusEl.textContent = "● Live";
    statusEl.className   = "status live";
    clearTranscript();
  });

  vapi.on("call-end", () => {
    statusEl.textContent = "Call ended — click the phone button to start again ↘";
    statusEl.className   = "status";
  });

  vapi.on("message", (msg) => {
    if (msg.type === "transcript" && msg.transcriptType === "final") {
      addTranscript(msg.role, msg.transcript);
    }
  });

  vapi.on("error", (err) => {
    console.error("Vapi error:", err);
    statusEl.textContent = "Error — check console";
    statusEl.className   = "status";
  });
}

function addTranscript(role, text) {
  transcriptBox.classList.remove("hidden");
  const entry = document.createElement("div");
  entry.className = "transcript-entry " + role;
  const icon = role === "assistant" ? "🤖" : "🎙️";
  entry.innerHTML = `<span class="role-icon">${icon}</span>${escapeHtml(text)}`;
  transcriptList.appendChild(entry);
  transcriptList.scrollTop = transcriptList.scrollHeight;
}

function clearTranscript() {
  transcriptList.innerHTML = "";
  transcriptBox.classList.add("hidden");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
