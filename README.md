# Verve Bespoke — Sub-Second Full-Duplex AI Voice Concierge 🎙️⚡

> **Overview:** Production-ready full-duplex conversational voice AI designed for direct e-commerce operations, sub-second latency, and deterministic tool execution.  
> **Key Metrics:** Sub-Second TTFA (~460ms LLM latency on Groq), Real-time Interruption (Barge-in), Deterministic Tool Calling on E-Commerce Operations.  
> **Stack Cost:** **100% Free ($0.00 spent, zero credit card requirements).**

---

## 🌟 Live Demo & Architecture

```
[ Browser WebRTC / Web Audio ]
              │ (Voice Input stream)
              ▼
   [ Speech-to-Text Layer ] ──────> Streaming Transcription
              │
              ▼ (Text Tokens)
   [ Groq Cloud LPU Engine ] ────> Llama / GPT-OSS (~300 tokens/sec)
              │                    • Tool Calling: lookup_order()
              │                    • Tool Calling: update_shipping_address()
              │                    • Tool Calling: request_alteration()
              │                    • Policy Guardrails: Alteration-only, No Shipped Address Changes
              ▼ (Conversational Response)
    [ Low-Latency Neural TTS ] ───> Edge-TTS Neural Audio Buffer
              │
              ▼
  [ Full-Duplex Web Audio ] ────> Instant Barge-in (Stops playback when user speaks)
```

---

## 🚀 How to Run Locally

### 1. Quick 1-Click Launch (Windows)
Double-click [`run.bat`](run.bat), or run in terminal:
```powershell
.\venv\Scripts\python.exe -m uvicorn server:app --app-dir backend --port 8000 --reload
```

### 2. Open the Web Application
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🧪 Verified Test Cases & Benchmarks

The agent was verified across realistic bespoke clothing scenarios:

### Test Case 1: Real-time Order Lookup (WISMO)
* **User:** *"Where is my order ORD-102?"*
* **Tool Executed:** `lookup_order(query='ORD-102')`
* **Agent Response:** *"Your order ORD-102 is on its way! It shipped via BlueDart Express and should arrive today by 7 PM at B-12 Sea View Apartments, Worli."*
* **Latency:** **467 ms LLM time** | **981 ms total roundtrip**

### Test Case 2: Live Address Mutation Before Dispatch
* **User:** *"Please update the shipping address for ORD-101 to 99 Palm Avenue, Bangalore"*
* **Tool Executed:** `update_shipping_address(order_id='ORD-101', new_address='99 Palm Avenue, Bangalore')`
* **Atelier Database:** In-memory record updated live on the screen!
* **Agent Response:** *"Your shipping address for Order ORD-101 has been updated to 99 Palm Avenue, Bangalore."*

### Test Case 3: Policy Guardrail Rejection on Shipped Items
* **User:** *"Please change shipping address for ORD-102 to Calangute, Goa"*
* **Tool Result:** Rejection (`Cannot update address because it has already been shipped with BlueDart Express.`)
* **Agent Response:** *"I’m sorry, but I can’t change the address for that order. It has already been shipped with BlueDart Express."*

### Test Case 4: Complimentary Alteration Scheduling
* **User:** *"My tuxedo shirt ORD-103 arrived, but the sleeves are 1 inch too long. Can I get an alteration?"*
* **Tool Executed:** `request_alteration(order_id='ORD-103', alteration_details='Sleeves need shortening by 1 inch')`
* **Agent Response:** *"Alteration ticket ALT-10301 created! Our courier will pick up the shirt from your address within 24-48 hours for refitting by our master tailors."*

---

## 🌐 100% Free Cloud Deployment Guide

### Deploying the Backend to Render.com (Free)
1. Push this repository to GitHub.
2. Go to [render.com](https://render.com) and click **New Web Service**.
3. Select your GitHub repository.
4. Set:
   * **Build Command:** `pip install -r backend/requirements.txt`
   * **Start Command:** `uvicorn server:app --app-dir backend --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   * `GROQ_API_KEY`
   * `LIVEKIT_URL`
   * `LIVEKIT_API_KEY`
   * `LIVEKIT_API_SECRET`
   * `DEEPGRAM_API_KEY`
6. Click **Deploy**. Render will generate a free public HTTPS URL (e.g., `https://verve-voice-agent.onrender.com`).

---

## 📁 File Structure

* `backend/`
  * [`server.py`](backend/server.py): FastAPI server, WebSocket voice stream, LiveKit token generator, and static web mount.
  * [`tools.py`](backend/tools.py): Deterministic tool functions and JSON schemas for function calling.
  * [`mock_data.py`](backend/mock_data.py): Custom bespoke atelier orders, customer profiles, and brand policies.
  * [`test_voice_agent.py`](backend/test_voice_agent.py): Automated pipeline benchmark test.
* `frontend/`
  * [`index.html`](frontend/index.html): Modern dark developer terminal UI with live waveform and order inspector.
  * [`app.js`](frontend/app.js): Web Audio streaming, real-time barge-in listener, and live ERP database sync.
* [`.env`](.env): Free cloud API keys.
* [`run.bat`](run.bat): 1-click Windows launcher.
