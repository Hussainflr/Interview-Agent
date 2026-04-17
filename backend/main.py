from fastapi import FastAPI
from backend.websocket import interview_ws_handler
from fastapi.responses import FileResponse 
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Interview Agent API is running 🚀"}



@app.get("/ui")
def ui():
    return FileResponse("frontend/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):  # ✅ MUST be typed
    await interview_ws_handler(websocket)