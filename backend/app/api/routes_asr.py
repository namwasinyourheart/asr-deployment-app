from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
# from app.services.inference import asr_infer
from app.services.inference_faster_whisper import asr_infer
from app.schemas.asr import ASRResponse
import tempfile
import shutil
import os

router = APIRouter()

@router.post("/asr/file", response_model=ASRResponse)
async def transcribe_audio_file(audio_file: UploadFile = File(...)):
    """Upload một file audio để transcribe"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            shutil.copyfileobj(audio_file.file, tmp)
            tmp_path = tmp.name
        result = asr_infer(tmp_path)
        return result
    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/asr/url", response_model=ASRResponse)
async def transcribe_audio_url(audio_url: str = Form(...)):
    """Truyền URL audio để transcribe"""
    if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    return asr_infer(audio_url)



@router.websocket("/asr/chunk")
async def asr_chunk(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            chunk_bytes = await websocket.receive_bytes()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(chunk_bytes)
                tmp_path = tmp.name

            result = asr_infer(tmp_path)
            await websocket.send_json({
                "partial": result.get("text", ""),
                "duration": result.get("duration", 0)
            })
    except WebSocketDisconnect:
        print("🔌 Client disconnected")
    # except Exception as e:
    #     print("Error:", e)
    #     try:
    #         await websocket.send_json({"error": str(e)})
    #     except:
    #         pass
    # finally:
    #     pass
