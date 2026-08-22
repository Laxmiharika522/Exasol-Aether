import os
from fastapi import FastAPI, UploadFile, File, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import requests
from dotenv import load_dotenv

# Import Orchestrator
from agents.orchestrator import Orchestrator

load_dotenv()

app = FastAPI(title="Aether Copilot API")

# Initialize Orchestrator globally
orch = Orchestrator()

# Ensure static folder exists
os.makedirs("frontend/static", exist_ok=True)

# Mount the static files (HTML, CSS, JS) at the root
app.mount("/app", StaticFiles(directory="frontend/static", html=True), name="static")

@app.post("/api/chat")
async def chat(payload: dict = Body(...)):
    """
    Accepts: {"prompt": "user question", "history": [{"role": "user", "content": "..."}]}
    """
    question = payload.get("prompt")
    chat_history = payload.get("history", [])
    
    if not question:
        return JSONResponse({"success": False, "error": "No prompt provided."})
        
    try:
        response = orch.answer(question, chat_history=chat_history)
        return JSONResponse(response)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/voice")
async def voice(file: UploadFile = File(...)):
    """
    Accepts an audio file upload and forwards it to Groq Whisper.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return JSONResponse({"success": False, "error": "GROQ_API_KEY is not set on the server."})
        
    try:
        audio_bytes = await file.read()
        
        files = {'file': (file.filename or 'audio.wav', audio_bytes, file.content_type or 'audio/wav')}
        data = {'model': 'whisper-large-v3-turbo'}
        headers = {'Authorization': f'Bearer {api_key}'}
        
        res = requests.post('https://api.groq.com/openai/v1/audio/transcriptions', headers=headers, files=files, data=data)
        res.raise_for_status()
        
        return JSONResponse({"success": True, "text": res.json().get('text', '')})
    except Exception as e:
        error_msg = str(e)
        try:
            error_msg = res.text
        except:
            pass
        return JSONResponse({"success": False, "error": error_msg})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
