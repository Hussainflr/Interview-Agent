from fastapi import FastAPI, WebSocket
from backend.websocket import interview_ws_handler

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Interview Agent API is running 🚀"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):  # ✅ MUST be typed
    await interview_ws_handler(websocket)