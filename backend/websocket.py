import numpy as np
from fastapi import WebSocket

from backend.pipeline import process_audio_array

buffer = []
session_id = None

async def interview_ws_handler(websocket: WebSocket):
    await websocket.accept()

    global buffer, session_id

    try:
        while True:
            chunk = await websocket.receive_bytes()

            # Convert Int16 → float32
            audio = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            buffer.append(audio)

            # Process every ~1 sec for lower latency
            if len(buffer) > 10:
                full_audio = np.concatenate(buffer)
                buffer = []

                response_audio, response_text, user_text, session_id = process_audio_array(full_audio, session_id)

                await websocket.send_json({"text": response_text, "user_text": user_text, "session_id": session_id})
                if response_audio:
                    await websocket.send_bytes(response_audio)

    except Exception as e:
        print("WebSocket closed:", e)
