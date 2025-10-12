from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from app.services.inference import asr_infer
from app.services.inference_ct2 import asr_infer as asr_infer_ct2
from app.services.postprocess import postprocess, load_spelling_vocab
from app.schemas.asr import ASRResponse, ASRRequest
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


@router.post("/asr_ct2/file", response_model=ASRResponse)
async def transcribe_audio_file_ct2(audio_file: UploadFile = File(...)):
    """Upload một file audio để transcribe"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            shutil.copyfileobj(audio_file.file, tmp)
            tmp_path = tmp.name
        result = asr_infer_ct2(tmp_path)
        return result
    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)



@router.post("/asr_ct2/file", response_model=ASRResponse)
async def transcribe_audio_file_ct2(
    audio_file: UploadFile = File(...),
    options: ASRRequest = Depends()
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            shutil.copyfileobj(audio_file.file, tmp)
            tmp_path = tmp.name

        result = asr_infer(
            tmp_path,
            enhance_speech=options.enhance_speech,
            postprocess_text=options.postprocess_text,
        )
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


@router.post("/asr_ct2/url", response_model=ASRResponse)
async def transcribe_audio_url_ct2(audio_url: str = Form(...)):
    """Truyền URL audio để transcribe"""
    if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    return asr_infer_ct2(audio_url)


@router.websocket("/asr/stream")
async def transcribe_audio_stream(websocket: WebSocket):
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
                "duration": result.get("duration", -1),
                "processing_time": result.get("processing_time", -1)
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

@router.websocket("/asr_ct2/stream")
async def transcribe_audio_stream_ct2(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            chunk_bytes = await websocket.receive_bytes()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(chunk_bytes)
                tmp_path = tmp.name

            result = asr_infer_ct2(tmp_path)
            await websocket.send_json({
                "partial": result.get("text", ""),
                "duration": result.get("duration", -1),
                "processing_time": result.get("processing_time", -1)
            })
    except WebSocketDisconnect:
        print("🔌 Client disconnected")


_vocab_map = None
def _ensure_vocab_map():
    global _vocab_map
    if _vocab_map is None:
        _vocab_map = load_spelling_vocab("/home/nampv1/projects/asr/asr-demo-app/backend/app/services/postprocessing/spell_corrections_dict.txt")

@router.post("/asr/postprocess")
async def postprocess_asr(text: str = Form(...)):
    """
    Phục hồi viết hoa và dấu câu (Case & Punctuation Restore).
    """
    try:
        _ensure_vocab_map()
        print(_vocab_map)
        restored = postprocess(text, _vocab_map)
        return {"input": text, "output": restored}
    except Exception as e:
        return {"error": str(e)}