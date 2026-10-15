import sys
import asyncio
import httpx
import edge_tts
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

async def test_speech_to_speech():
    print("=" * 60)
    print("🎙️ Testing Speech-to-Speech End-to-End (/api/voice-turn)")
    print("=" * 60)

    # 1. Generate sample voice audio file: "Where is my order ORD-101?"
    print("1. Synthesizing sample voice input audio using Edge-TTS...")
    comm = edge_tts.Communicate("Where is my order ORD 101?", voice="en-US-GuyNeural")
    audio_bytes = bytearray()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
    print(f"   Generated {len(audio_bytes)} bytes of spoken audio.")

    # 2. Send to /api/voice-turn endpoint
    print("2. Sending audio to /api/voice-turn...")
    t0 = time.time()
    async with httpx.AsyncClient() as client:
        files = {"file": ("voice_test.mp3", bytes(audio_bytes), "audio/mpeg")}
        res = await client.post("http://127.0.0.1:8000/api/voice-turn", files=files, timeout=25.0)

    total_time = int((time.time() - t0) * 1000)

    if res.status_code == 200:
        data = res.json()
        print("\n✅ SPEECH-TO-SPEECH SUCCESS!")
        print(f"  🗣️ Deepgram STT Heard: \"{data['user_transcript']}\"")
        print(f"  🤖 Agent Voice Reply: \"{data['reply']}\"")
        if data.get("executed_tools"):
            print(f"  ⚡ Tools Executed: {data['executed_tools']}")
        print(f"  🔊 Returned Audio Size: {len(data['audio_base64'])} base64 chars")
        print(f"  ⏱️ Latency Waterfall: STT={data['latency']['stt_ms']}ms | LLM={data['latency']['llm_ms']}ms | TTS={data['latency']['tts_ms']}ms | Total={data['latency']['total_ttfa_ms']}ms")
    else:
        print(f"❌ Failed: HTTP {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(test_speech_to_speech())
