import os
import json
import time
import asyncio
import io
from pathlib import Path
from typing import Dict, Any, List

import base64
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from groq import AsyncGroq
import edge_tts
try:
    from livekit import api as livekit_api
except ImportError:
    livekit_api = None

from mock_data import ORDERS, CUSTOMERS, BRAND_INFO
from tools import TOOLS_SCHEMA, TOOL_FUNCTIONS, lookup_order

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# System prompt tuned specifically for conversational voice interactions
SYSTEM_PROMPT = f"""You are the real-time AI Voice Concierge for '{BRAND_INFO['name']}', a luxury custom bespoke clothing brand.
You assist clients calling about custom-tailored suits, blazers, shirts, fittings, and order statuses.

Brand Policies to Strictly Follow:
- Specialty: {BRAND_INFO['specialty']}
- Turnaround Time: {BRAND_INFO['turnaround_time']}
- Alteration Policy: {BRAND_INFO['alteration_policy']}
- Address Change: Allowed anytime before the order is SHIPPED. If already SHIPPED or DELIVERED, politely decline address changes.
- Cancellation: Strictly prohibited once fabric cutting starts (IN_PRODUCTION).

Voice Interaction Guidelines:
1. Speak naturally, warmly, and concisely (1 to 2 sentences per response). Never read markdown, bullet points, or raw JSON keys over voice.
2. If the user mentions an order or their phone number, use the `lookup_order` tool immediately.
3. If the user requests an address change, call `update_shipping_address`.
4. If a delivered garment doesn't fit, offer a complimentary alteration and call `request_alteration`.
5. If the client is upset or needs an impossible exception, call `escalate_to_master_tailor`.
"""

app = FastAPI(title="Sub-Second Voice Support Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = AsyncGroq(api_key=GROQ_API_KEY)


# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "livekit_configured": bool(LIVEKIT_URL and LIVEKIT_API_KEY and LIVEKIT_API_SECRET),
        "groq_configured": bool(GROQ_API_KEY),
        "deepgram_configured": bool(DEEPGRAM_API_KEY),
    }


@app.get("/api/orders")
async def get_orders():
    """Returns the current mock order database for the inspector UI."""
    return ORDERS


@app.get("/api/livekit/token")
async def get_livekit_token(room: str = "concierge-room", participant_name: str = "Client"):
    """Generates a secure LiveKit Cloud access token for the browser client."""
    if not (LIVEKIT_API_KEY and LIVEKIT_API_SECRET):
        raise HTTPException(status_code=500, detail="LiveKit credentials not configured in .env")

    token = livekit_api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(participant_name) \
        .with_name(participant_name) \
        .with_grants(livekit_api.VideoGrants(
            room_join=True,
            room=room,
            can_publish=True,
            can_subscribe=True
        ))

    return {
        "token": token.to_jwt(),
        "url": LIVEKIT_URL,
        "room": room,
        "participant": participant_name
    }


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


@app.post("/api/chat")
async def text_chat_endpoint(req: ChatRequest):
    """
    Direct low-latency text/tool API endpoint using Groq Llama 3.3 70B.
    Used for testing tools and fallback web chat.
    """
    start_time = time.time()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + req.history
    messages.append({"role": "user", "content": req.message})

    response = await groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto",
        temperature=0.4,
        max_tokens=250
    )

    choice = response.choices[0]
    llm_ms = int((time.time() - start_time) * 1000)
    executed_tools = []

    # Check for tool call
    if choice.message.tool_calls:
        for tool_call in choice.message.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            if func_name in TOOL_FUNCTIONS:
                tool_res = TOOL_FUNCTIONS[func_name](**args)
                executed_tools.append({"tool": func_name, "args": args, "result": tool_res})

                # Follow up with tool result
                messages.append(choice.message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_res)
                })

        # Second LLM call for conversational voice response
        followup = await groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.4,
            max_tokens=200
        )
        reply = followup.choices[0].message.content
    else:
        reply = choice.message.content

    # Synthesize Neural Speech Audio
    t_tts0 = time.time()
    communicate = edge_tts.Communicate(reply, voice="en-US-ChristopherNeural", rate="+10%")
    tts_buffer = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            tts_buffer.extend(chunk["data"])
    tts_ms = int((time.time() - t_tts0) * 1000)
    audio_b64 = base64.b64encode(bytes(tts_buffer)).decode("utf-8")

    total_ms = int((time.time() - start_time) * 1000)

    return {
        "reply": reply,
        "executed_tools": executed_tools,
        "audio_base64": audio_b64,
        "latency_ms": total_ms,
        "llm_ms": llm_ms,
        "tts_ms": tts_ms
    }


async def transcribe_with_deepgram(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """Sends raw audio bytes to Deepgram Nova-2 Cloud API for fast transcription."""
    if not DEEPGRAM_API_KEY:
        return ""
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": mime_type
            }
            res = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&language=en",
                headers=headers,
                content=audio_bytes,
                timeout=12.0
            )
            if res.status_code == 200:
                data = res.json()
                channels = data.get("results", {}).get("channels", [])
                if channels:
                    alts = channels[0].get("alternatives", [])
                    if alts:
                        return alts[0].get("transcript", "").strip()
    except Exception as e:
        print(f"Deepgram transcription error: {e}")
    return ""


@app.post("/api/voice-turn")
async def voice_turn_endpoint(file: UploadFile = File(...)):
    """
    End-to-End Speech-to-Speech API:
    1. Audio in -> Deepgram STT (~120ms)
    2. Transcript -> Groq LPU LLM with Tool Calling (~450ms)
    3. Reply -> Neural Edge-TTS (~250ms)
    4. Returns JSON with reply, user_transcript, tools, latency, and audio_base64
    """
    t_start = time.time()
    audio_bytes = await file.read()
    mime = file.content_type or "audio/webm"

    # Step 1: Deepgram STT
    t_stt_start = time.time()
    user_transcript = await transcribe_with_deepgram(audio_bytes, mime_type=mime)
    stt_ms = int((time.time() - t_stt_start) * 1000)

    if not user_transcript:
        return JSONResponse(
            status_code=400,
            content={"error": "No clear speech detected in audio. Please speak a little louder or closer to the mic."}
        )

    # Step 2: Groq LLM with Tool Execution
    t_llm_start = time.time()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_transcript}
    ]

    response = await groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto",
        temperature=0.3,
        max_tokens=200
    )

    choice = response.choices[0]
    executed_tools = []

    if choice.message.tool_calls:
        for tool_call in choice.message.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            if func_name in TOOL_FUNCTIONS:
                tool_res = TOOL_FUNCTIONS[func_name](**args)
                executed_tools.append({"tool": func_name, "args": args, "result": tool_res})

                messages.append(choice.message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_res)
                })

        followup = await groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.3,
            max_tokens=150
        )
        reply_text = followup.choices[0].message.content
    else:
        reply_text = choice.message.content

    llm_ms = int((time.time() - t_llm_start) * 1000)

    # Step 3: Neural Edge-TTS Synthesis
    t_tts_start = time.time()
    communicate = edge_tts.Communicate(reply_text, voice="en-US-ChristopherNeural", rate="+10%")
    tts_buffer = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            tts_buffer.extend(chunk["data"])

    tts_ms = int((time.time() - t_tts_start) * 1000)
    total_ttfa = int((time.time() - t_start) * 1000)

    audio_b64 = base64.b64encode(bytes(tts_buffer)).decode("utf-8")

    return {
        "user_transcript": user_transcript,
        "reply": reply_text,
        "executed_tools": executed_tools,
        "audio_base64": audio_b64,
        "latency": {
            "stt_ms": stt_ms,
            "llm_ms": llm_ms,
            "tts_ms": tts_ms,
            "total_ttfa_ms": total_ttfa
        }
    }


# -----------------------------------------------------------------------------
# Real-Time Voice WebSocket with Streaming Audio & Interruption (Barge-in)
# -----------------------------------------------------------------------------

@app.websocket("/api/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    Sub-second bidirectional Voice WebSocket.
    Features:
    - Receives user transcripts / audio
    - Streams Groq Llama 3.3 70B tokens
    - Synthesizes low-latency audio via Edge-TTS
    - Handles instant barge-in / interruption
    """
    await websocket.accept()
    conversation_history: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    current_playback_task: asyncio.Task = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            event = json.loads(raw_data)
            event_type = event.get("type")

            # 1. User interruption / barge-in event
            if event_type == "barge_in":
                if current_playback_task and not current_playback_task.done():
                    current_playback_task.cancel()
                await websocket.send_text(json.dumps({
                    "type": "playback_cancelled",
                    "message": "User interrupted. Speech generation aborted."
                }))
                continue

            # 2. User speech transcript received (from client-side STT / Deepgram)
            elif event_type == "user_transcript":
                user_text = event.get("text", "").strip()
                if not user_text:
                    continue

                t_start = time.time()
                conversation_history.append({"role": "user", "content": user_text})

                # Stream LLM from Groq
                llm_response = await groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=conversation_history,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                    temperature=0.4,
                    max_tokens=200
                )

                choice = llm_response.choices[0]
                t_llm = time.time()
                llm_ms = int((t_llm - t_start) * 1000)

                executed_tools = []
                if choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        func_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        if func_name in TOOL_FUNCTIONS:
                            res = TOOL_FUNCTIONS[func_name](**args)
                            executed_tools.append({"tool": func_name, "args": args, "result": res})

                            conversation_history.append(choice.message)
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(res)
                            })

                    followup = await groq_client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=conversation_history,
                        temperature=0.4,
                        max_tokens=180
                    )
                    reply_text = followup.choices[0].message.content
                else:
                    reply_text = choice.message.content

                conversation_history.append({"role": "assistant", "content": reply_text})

                # Synthesize TTS using free neural voice
                t_tts_start = time.time()
                communicate = edge_tts.Communicate(reply_text, voice="en-US-ChristopherNeural", rate="+10%")
                audio_buffer = bytearray()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buffer.extend(chunk["data"])

                tts_ms = int((time.time() - t_tts_start) * 1000)
                total_ttfa = int((time.time() - t_start) * 1000)

                # Send response packet with audio and latency metrics
                await websocket.send_text(json.dumps({
                    "type": "agent_response",
                    "text": reply_text,
                    "tools": executed_tools,
                    "latency": {
                        "total_ttfa_ms": total_ttfa,
                        "llm_ms": llm_ms,
                        "tts_ms": tts_ms
                    }
                }))

                # Send binary audio bytes
                await websocket.send_bytes(bytes(audio_buffer))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))


frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
