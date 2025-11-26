# curl -X POST "https://ai.vnpost.vn/voiceai/core/stt/v1/file" \
#     -F "audio_file=@/path/to/your/audio/file.wav" \
#     -F "enhance_speech=true" \
#     -F "postprocess_text=true"


# curl -X POST "https://ai.vnpost.vn/voiceai/core/asr/v1/post_process_text" \
#     -H "Content-Type: application/json" \
#     -d '{"text": "Dưới đây là kết quả đã được đưa vào quá trình đưa vào quá trình đưa vào quá trình đưa vào quá trình đưa vào quá trình post-processing"}'



import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from app.services.inference import asr_infer as asr_infer
from app.services.postprocess_text import postprocess_text

from app.schemas.asr import ASRResponse, ASRRequest
import tempfile
import aiofiles
import os



router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = (".wav", ".mp3", ".flac", ".m4a")

@router.post("/file", response_model=ASRResponse)
async def transcribe_audio_file(
    audio_file: UploadFile = File(...),
    enhance_speech: bool = Form(True),
    postprocess_text: bool = Form(True),
):
    # Validate file type
    if not audio_file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}")

    # Tạo ASRRequest object thủ công — không đụng schema
    options = ASRRequest(
        enhance_speech=enhance_speech,
        postprocess_text=postprocess_text,
    )

    # Tạo file tạm
    suffix = os.path.splitext(audio_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name

    try:
        # Ghi file upload vào temp file
        async with aiofiles.open(tmp_path, "wb") as out_file:
            while chunk := await audio_file.read(1024 * 1024):
                await out_file.write(chunk)

        logger.info(f"Saved uploaded file to temp path: {tmp_path}, size: {os.path.getsize(tmp_path)} bytes")

        # Chạy inference
        try:
            result = asr_infer(
                tmp_path,
                do_enhance_speech=options.enhance_speech,
                do_postprocess_text=options.postprocess_text,
                milliseconds=True,
            )
        except Exception as e:
            logger.error(f"ASR inference failed: {e}")
            raise HTTPException(status_code=500, detail=f"ASR inference failed: {str(e)}")

        return result

    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.info(f"Deleted temp file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")

@router.post("/", response_model=ASRResponse)
async def transcribe_audio_file(
    audio_file: UploadFile = File(...),
    enhance_speech: bool = Form(True),
    postprocess_text: bool = Form(True),
):
    # Validate file type
    if not audio_file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}")

    # Tạo ASRRequest object thủ công — không đụng schema
    options = ASRRequest(
        enhance_speech=enhance_speech,
        postprocess_text=postprocess_text,
    )

    # Tạo file tạm
    suffix = os.path.splitext(audio_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name

    try:
        # Ghi file upload vào temp file
        async with aiofiles.open(tmp_path, "wb") as out_file:
            while chunk := await audio_file.read(1024 * 1024):
                await out_file.write(chunk)

        logger.info(f"Saved uploaded file to temp path: {tmp_path}, size: {os.path.getsize(tmp_path)} bytes")

        # Chạy inference
        try:
            result = asr_infer(
                tmp_path,
                do_enhance_speech=options.enhance_speech,
                do_postprocess_text=options.postprocess_text,
                milliseconds=True,
            )
        except Exception as e:
            logger.error(f"ASR inference failed: {e}")
            raise HTTPException(status_code=500, detail=f"ASR inference failed: {str(e)}")

        return result

    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.info(f"Deleted temp file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")


@router.post("/postprocess_text", response_model=ASRResponse)
async def postprocess_text_endpoint(text: str = Form(...)):
    """Truyền text để postprocess"""
    from app.services.postprocess_text import postprocess_text
    processed_text = postprocess_text(text)["text"]
    return {"text": processed_text}



@router.post("/url", response_model=ASRResponse)
async def transcribe_audio_url(audio_url: str = Form(...)):
    """Truyền URL audio để transcribe"""
    if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    return asr_infer(audio_url)



@router.websocket("/stream")
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
                "total_processing_time": result.get("total_processing_time", -1)
            })
    except WebSocketDisconnect:
        print("🔌 Client disconnected")
