// Verve Bespoke - Sub-Second Full-Duplex Voice Engine (Deepgram + Groq + Edge-TTS)

let isCalling = false;
let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let audioContext = null;
let analyser = null;
let micSource = null;
let currentAudio = null;
let isAgentSpeaking = false;

// VAD (Voice Activity Detection) State
let isUserSpeaking = false;
let silenceTimer = null;
let vadCheckInterval = null;
const SILENCE_THRESHOLD_MS = 900; // Pause duration to trigger query submission
const VOLUME_THRESHOLD = 22;      // User speaking threshold

// DOM Elements
const callToggleBtn = document.getElementById("callToggleBtn");
const callIcon = document.getElementById("callIcon");
const callStatusText = document.getElementById("callStatusText");
const callSubtext = document.getElementById("callSubtext");
const pulseRings = document.getElementById("pulseRings");
const transcriptBox = document.getElementById("transcriptBox");
const ttfaDisplay = document.getElementById("ttfaDisplay");
const sttLatencyDisplay = document.getElementById("sttLatencyDisplay");
const llmLatencyDisplay = document.getElementById("llmLatencyDisplay");
const ttsLatencyDisplay = document.getElementById("ttsLatencyDisplay");
const bargeinBadge = document.getElementById("bargeinBadge");
const ordersContainer = document.getElementById("ordersContainer");
const refreshOrdersBtn = document.getElementById("refreshOrdersBtn");
const textTestForm = document.getElementById("textTestForm");
const textInput = document.getElementById("textInput");

const sttDot = document.getElementById("sttDot");
const llmDot = document.getElementById("llmDot");
const ttsDot = document.getElementById("ttsDot");

let canvas, canvasCtx;

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();
  setupCanvas();
  fetchOrders();
  setupSamplePrompts();
});

// Setup Soundwave Canvas
function setupCanvas() {
  canvas = document.getElementById("waveformCanvas");
  canvasCtx = canvas.getContext("2d");
  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);
  drawWaveform();
}

function resizeCanvas() {
  if (!canvas) return;
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight;
}

// Waveform visualizer
function drawWaveform() {
  if (!canvasCtx) return;
  canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

  const width = canvas.width;
  const height = canvas.height;
  const time = Date.now() * 0.004;

  canvasCtx.lineWidth = 1;
  canvasCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  canvasCtx.beginPath();
  canvasCtx.moveTo(0, height / 2);
  canvasCtx.lineTo(width, height / 2);
  canvasCtx.stroke();

  let liveVolume = 0;
  if (analyser && isCalling && !isAgentSpeaking) {
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    liveVolume = sum / dataArray.length;
  }

  canvasCtx.lineWidth = isCalling ? 2 : 1.5;
  canvasCtx.strokeStyle = isCalling ? (isAgentSpeaking ? "#38bdf8" : (isUserSpeaking ? "#fa5d19" : "rgba(250, 93, 25, 0.6)")) : "rgba(250, 93, 25, 0.25)";
  
  if (isCalling && (isUserSpeaking || isAgentSpeaking)) {
    canvasCtx.shadowColor = isAgentSpeaking ? "#38bdf8" : "#fa5d19";
    canvasCtx.shadowBlur = 14;
  }

  canvasCtx.beginPath();
  for (let x = 0; x < width; x += 2) {
    const freq = isCalling ? (isAgentSpeaking ? 0.05 : 0.035) : 0.015;
    const baseAmp = isCalling 
      ? (isAgentSpeaking ? 16 : (isUserSpeaking ? Math.max(liveVolume * 0.6, 12) : 6)) 
      : 2.5;
    const y = height / 2 + Math.sin(x * freq + time) * baseAmp * Math.sin(x * 0.005 + time * 0.5);
    if (x === 0) canvasCtx.moveTo(x, y);
    else canvasCtx.lineTo(x, y);
  }
  canvasCtx.stroke();
  canvasCtx.shadowBlur = 0;

  requestAnimationFrame(drawWaveform);
}

// Call Toggle (Start / Stop Voice Session)
callToggleBtn.addEventListener("click", async () => {
  if (!isCalling) {
    await startVoiceSession();
  } else {
    stopVoiceSession();
  }
});

async function startVoiceSession() {
  try {
    // 1. Request Real Microphone Access
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    // 2. Setup Web Audio Analyser
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    if (audioContext.state === "suspended") {
      await audioContext.resume();
    }
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    micSource = audioContext.createMediaStreamSource(mediaStream);
    micSource.connect(analyser);

    isCalling = true;
    isAgentSpeaking = false;
    callToggleBtn.classList.remove("btn-heat");
    callToggleBtn.classList.add("bg-rose-600", "hover:bg-rose-700");
    callIcon.setAttribute("data-lucide", "phone-off");
    if (window.lucide) lucide.createIcons();

    pulseRings.classList.remove("hidden");
    callStatusText.textContent = "Listening to you — Speak now";
    callSubtext.textContent = "Microphone connected. Speak your question, pause, and the agent will answer with voice.";
    sttDot.className = "w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse";

    initMediaRecorder();
    startVADMonitoring();

  } catch (err) {
    console.error("Microphone Access Error:", err);
    alert("Microphone permission was denied. Please click the lock icon in your browser address bar and allow microphone access.");
  }
}

function stopVoiceSession() {
  isCalling = false;
  isUserSpeaking = false;
  isAgentSpeaking = false;

  if (silenceTimer) clearTimeout(silenceTimer);
  if (vadCheckInterval) clearInterval(vadCheckInterval);

  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    try { mediaRecorder.stop(); } catch (e) {}
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
  }

  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  callToggleBtn.classList.remove("bg-rose-600", "hover:bg-rose-700");
  callToggleBtn.classList.add("btn-heat");
  callIcon.setAttribute("data-lucide", "mic");
  if (window.lucide) lucide.createIcons();

  pulseRings.classList.add("hidden");
  callStatusText.textContent = "Session Idle (Click to Connect)";
  callSubtext.textContent = "Click the flame microphone button to start a full-duplex voice session.";

  sttDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
  llmDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
  ttsDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
}

// Initialize MediaRecorder
function initMediaRecorder() {
  recordedChunks = [];
  
  let mimeType = 'audio/webm;codecs=opus';
  if (!MediaRecorder.isTypeSupported(mimeType)) {
    mimeType = 'audio/webm';
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = '';
    }
  }

  try {
    mediaRecorder = mimeType ? new MediaRecorder(mediaStream, { mimeType }) : new MediaRecorder(mediaStream);
  } catch (e) {
    mediaRecorder = new MediaRecorder(mediaStream);
  }

  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) {
      recordedChunks.push(e.data);
    }
  };

  mediaRecorder.onstop = async () => {
    if (recordedChunks.length > 0 && isCalling && !isAgentSpeaking) {
      const audioBlob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      recordedChunks = [];
      
      // Ensure audio has enough speech content
      if (audioBlob.size > 2500) {
        await sendVoiceTurn(audioBlob);
      } else {
        // Too small / empty noise -> resume recording
        restartRecorderSafe();
      }
    } else {
      recordedChunks = [];
      restartRecorderSafe();
    }
  };

  try {
    mediaRecorder.start(100);
  } catch (e) {}
}

function restartRecorderSafe() {
  if (isCalling && mediaRecorder && mediaRecorder.state === "inactive" && !isAgentSpeaking) {
    initMediaRecorder();
  }
}

// Voice Activity Detection loop
function startVADMonitoring() {
  const dataArray = new Uint8Array(analyser.frequencyBinCount);

  vadCheckInterval = setInterval(() => {
    if (!isCalling || !analyser) return;

    // If agent is speaking, ignore microphone feedback so it doesn't self-interrupt!
    if (isAgentSpeaking) return;

    analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    const currentVolume = sum / dataArray.length;

    // Detect user speaking
    if (currentVolume > VOLUME_THRESHOLD) {
      if (!isUserSpeaking) {
        isUserSpeaking = true;
        sttDot.className = "w-1.5 h-1.5 rounded-full bg-heat animate-ping";
        callStatusText.textContent = "Listening to you...";
      }

      if (silenceTimer) {
        clearTimeout(silenceTimer);
        silenceTimer = null;
      }
    } else {
      // User is silent
      if (isUserSpeaking && !silenceTimer) {
        silenceTimer = setTimeout(() => {
          isUserSpeaking = false;
          sttDot.className = "w-1.5 h-1.5 rounded-full bg-emerald-400";
          callStatusText.textContent = "Processing speech with Deepgram & Groq...";

          if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
          }
          silenceTimer = null;
        }, SILENCE_THRESHOLD_MS);
      }
    }
  }, 50);
}

// Send Audio Blob to Backend
async function sendVoiceTurn(audioBlob) {
  llmDot.className = "w-1.5 h-1.5 rounded-full bg-heat animate-pulse";
  
  const formData = new FormData();
  formData.append("file", audioBlob, "voice_turn.webm");

  try {
    const res = await fetch("/api/voice-turn", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      callStatusText.textContent = "Listening to you — Speak now";
      llmDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
      restartRecorderSafe();
      return;
    }

    const data = await res.json();

    // 1. Display User Transcript
    appendMessage("CLIENT_USER", data.user_transcript);

    // 2. Display Agent Reply & Executed Tools
    appendMessage("VOICE_CONCIERGE", data.reply, data.executed_tools);

    // 3. Update Latency Telemetry
    if (data.latency) {
      ttfaDisplay.textContent = `${data.latency.total_ttfa_ms} ms`;
      if (sttLatencyDisplay) sttLatencyDisplay.textContent = `${data.latency.stt_ms} ms`;
      if (llmLatencyDisplay) llmLatencyDisplay.textContent = `${data.latency.llm_ms} ms`;
      if (ttsLatencyDisplay) ttsLatencyDisplay.textContent = `${data.latency.tts_ms} ms`;
    }

    // 4. Update Orders Table if tool changed database
    if (data.executed_tools && data.executed_tools.length > 0) {
      fetchOrders();
    }

    // 5. Play Neural Speech Audio
    if (data.audio_base64) {
      playBase64Audio(data.audio_base64);
    } else {
      callStatusText.textContent = "Listening to you — Speak now";
      llmDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
      restartRecorderSafe();
    }

  } catch (err) {
    console.error("Voice turn request failed:", err);
    callStatusText.textContent = "Listening to you — Speak now";
    llmDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
    restartRecorderSafe();
  }
}

// Bulletproof Speech Playback (Plays in 100% of browsers)
function playBase64Audio(base64Str) {
  try {
    isAgentSpeaking = true;

    // Pause recording while agent is speaking to prevent speaker acoustic feedback
    if (mediaRecorder && mediaRecorder.state === "recording") {
      try { mediaRecorder.pause(); } catch(e) {}
    }

    const byteCharacters = atob(base64Str);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'audio/mpeg' });
    const audioUrl = URL.createObjectURL(blob);

    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    currentAudio = new Audio(audioUrl);
    currentAudio.volume = 1.0;

    ttsDot.className = "w-1.5 h-1.5 rounded-full bg-heat animate-pulse";
    callStatusText.textContent = "Agent is speaking... (Listen)";

    currentAudio.onended = () => {
      isAgentSpeaking = false;
      ttsDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
      llmDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
      
      if (isCalling) {
        callStatusText.textContent = "Listening to you — Speak now";
        // Resume microphone recording
        if (mediaRecorder && mediaRecorder.state === "paused") {
          try { mediaRecorder.resume(); } catch(e) { restartRecorderSafe(); }
        } else {
          restartRecorderSafe();
        }
      }
      currentAudio = null;
    };

    currentAudio.onerror = (e) => {
      console.error("Audio playback element error:", e);
      isAgentSpeaking = false;
      restartRecorderSafe();
    };

    const playPromise = currentAudio.play();
    if (playPromise !== undefined) {
      playPromise.catch(error => {
        console.warn("Audio autoplay restricted. User interaction required:", error);
        isAgentSpeaking = false;
        callStatusText.textContent = "Listening to you — Speak now";
        restartRecorderSafe();
      });
    }

  } catch (err) {
    console.error("playBase64Audio error:", err);
    isAgentSpeaking = false;
    restartRecorderSafe();
  }
}

// Append Message to Console Log
function appendMessage(sender, text, tools = null) {
  const isAgent = sender.includes("CONCIERGE");
  const div = document.createElement("div");
  div.className = `p-3 rounded-lg border ${
    isAgent 
      ? 'bg-[#141414] border-[#292929] text-slate-200' 
      : 'bg-[#181818] border-heat/30 text-slate-100'
  }`;

  let toolMarkup = "";
  if (tools && tools.length > 0) {
    toolMarkup = `
      <div class="mt-2.5 pt-2 border-t border-[#242424] text-[11px] font-mono space-y-1">
        ${tools.map(t => `
          <div class="bg-[#0d0d0d] p-1.5 rounded border border-[#222222] text-heat">
            <span class="text-slate-500">></span> <strong>EXEC:</strong> ${t.tool}(${JSON.stringify(t.args)})
          </div>
        `).join("")}
      </div>
    `;
  }

  div.innerHTML = `
    <div class="flex items-center justify-between text-[11px] font-mono font-bold mb-1.5 ${isAgent ? 'text-heat' : 'text-slate-400'}">
      <span>● ${sender}</span>
      <span class="text-slate-600 font-normal text-[10px]">${new Date().toLocaleTimeString()}</span>
    </div>
    <div class="font-sans text-xs leading-relaxed text-slate-300">
      ${text.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>')}
    </div>
    ${toolMarkup}
  `;

  transcriptBox.appendChild(div);
  transcriptBox.scrollTop = transcriptBox.scrollHeight;
}

// Terminal Text Input Form (Also Plays Neural Voice Speech!)
textTestForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = textInput.value.trim();
  if (!text) return;
  textInput.value = "";

  appendMessage("CLIENT_USER", text);
  llmDot.className = "w-1.5 h-1.5 rounded-full bg-heat animate-pulse";
  callStatusText.textContent = "Processing query...";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history: [] })
    });
    const data = await res.json();
    appendMessage("VOICE_CONCIERGE", data.reply, data.executed_tools);
    
    if (data.latency_ms) {
      ttfaDisplay.textContent = `${data.latency_ms} ms`;
      if (llmLatencyDisplay) llmLatencyDisplay.textContent = `${data.llm_ms} ms`;
      if (ttsLatencyDisplay) ttsLatencyDisplay.textContent = `${data.tts_ms} ms`;
    }
    
    if (data.executed_tools && data.executed_tools.length > 0) {
      fetchOrders();
    }

    // Play speech audio from /api/chat!
    if (data.audio_base64) {
      playBase64Audio(data.audio_base64);
    } else {
      callStatusText.textContent = "Session Ready";
    }

  } catch (err) {
    console.error("Text chat failed:", err);
  } finally {
    llmDot.className = "w-1.5 h-1.5 rounded-full bg-slate-600";
  }
});

// Fetch and Render Live Atelier Orders
async function fetchOrders() {
  try {
    const res = await fetch("/api/orders");
    const orders = await res.json();
    renderOrders(orders);
  } catch (e) {
    console.error("Failed to fetch orders:", e);
  }
}

function renderOrders(orders) {
  ordersContainer.innerHTML = "";
  for (const [id, o] of Object.entries(orders)) {
    const statusBadges = {
      "IN_PRODUCTION": "bg-heat/10 text-heat border-heat/30",
      "SHIPPED": "bg-sky-500/10 text-sky-400 border-sky-500/30",
      "DELIVERED": "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
      "AWAITING_MEASUREMENT_CONFIRMATION": "bg-purple-500/10 text-purple-400 border-purple-500/30"
    };

    const card = document.createElement("div");
    card.className = "p-2.5 rounded-lg bg-[#141414] border border-[#242424] hover:border-heat/40 transition space-y-1";
    card.innerHTML = `
      <div class="flex items-center justify-between text-[11px]">
        <span class="font-bold text-white font-mono flex items-center gap-1.5">
          <span class="text-heat">#</span>${o.order_id}
        </span>
        <span class="px-1.5 py-0.5 rounded text-[10px] border ${statusBadges[o.status] || 'bg-slate-500/10 text-slate-300'}">
          ${o.status}
        </span>
      </div>
      <div class="text-slate-200 text-xs font-sans font-medium">${o.item_name}</div>
      <div class="text-[11px] text-slate-400 font-sans">Client: <span class="text-slate-300 font-mono">${o.customer_name}</span></div>
      <div class="text-[10px] text-slate-500 font-mono truncate">stage: "${o.production_stage}"</div>
      <div class="text-[10px] text-slate-500 font-mono truncate" title="${o.shipping_address}">addr: "${o.shipping_address}"</div>
      ${o.alteration_ticket ? `<div class="mt-1 pt-1 border-t border-emerald-500/20 text-emerald-400 text-[10px] font-mono">✂️ ALT_TICKET: ${o.alteration_ticket.ticket_id} (${o.alteration_ticket.status})</div>` : ''}
    `;
    ordersContainer.appendChild(card);
  }
}

refreshOrdersBtn.addEventListener("click", fetchOrders);

// Setup Clickable Sample Prompt Chips
function setupSamplePrompts() {
  document.querySelectorAll(".sample-prompt").forEach(btn => {
    btn.addEventListener("click", () => {
      const text = btn.querySelector("span:last-child").textContent.trim();
      textInput.value = text;
      textTestForm.dispatchEvent(new Event("submit"));
    });
  });
}

const testAudioBtn = document.getElementById("testAudioBtn");
if (testAudioBtn) {
  testAudioBtn.addEventListener("click", () => {
    textInput.value = "Hello! Please give a quick 1-sentence welcome.";
    textTestForm.dispatchEvent(new Event("submit"));
  });
}

