import numpy as np
import soundfile as sf
from fastapi import WebSocket

from backend.pipeline import process_audio_array

buffer = []

async def interview_ws_handler(websocket: WebSocket):
    await websocket.accept()

    global buffer

    try:
        while True:
            chunk = await websocket.receive_bytes()

            # Convert Int16 → float32
            audio = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            buffer.append(audio)

            # Process every ~2 sec
            if len(buffer) > 20:
                full_audio = np.concatenate(buffer)
                buffer = []

                # Send to pipeline (NO FILE CONVERSION)
                response_audio, response_text = process_audio_array(full_audio)

                await websocket.send_json({"text": response_text})
                await websocket.send_bytes(response_audio)

    except Exception as e:
        print("WebSocket closed:", e)