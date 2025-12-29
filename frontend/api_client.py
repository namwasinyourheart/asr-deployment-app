import os
import time
import httpx
import asyncio
import websockets
import json
import soundfile as sf
import io
import numpy as np

# API_FILE_ENDPOINT = "http://127.0.0.1:13081/api/v1/asr/file"
# API_FILE_ENDPOINT = "http://127.0.0.1:13081/api/v1/asr_ct2/file"
API_FILE_ENDPOINT = "https://ai.vnpost.vn/voiceai/core/stt/v1/file"
API_URL_ENDPOINT = "https://ai.vnpost.vn/voiceai/asr/asr/v1/url"
WS_ENDPOINT = "ws://ai.vnpost.vn/voiceai/asr/asr/v1/stream"

async def download_audio(url: str, temp_dir: str = "/tmp") -> str:
    """Tải file âm thanh từ URL về thư mục tạm"""
    try:
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, os.path.basename(url).split("?")[0] or f"audio_{int(time.time())}.wav")
        
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        return file_path
    except Exception as e:
        raise Exception(f"Lỗi khi tải file âm thanh: {str(e)}")

async def transcribe_async(audio_source: str, audio_file_or_url: str):
    """Gọi API HTTP để transcribe file hoặc URL"""
    transcript, duration, processing_time, error_message = "", 0, 0, ""
    start_time = time.time()
    
    try:
        # Determine if the input is a URL or a local file path
        is_url = audio_file_or_url.startswith(("http://", "https://"))

        async with httpx.AsyncClient(timeout=120) as client:
            file_to_transcribe = audio_file_or_url
            temp_file_to_delete = None

            # If it's a URL, download it first
            if audio_source == "URL" and is_url:
                try:
                    temp_file = await download_audio(audio_file_or_url)
                    file_to_transcribe = temp_file
                    temp_file_to_delete = temp_file
                except Exception as e:
                    error_message = f"Lỗi khi xử lý URL: {str(e)}"
                    return "", 0, 0, error_message
            
            # Transcribe the local file (either original or downloaded)
            with open(file_to_transcribe, "rb") as f:
                files = {"audio_file": (os.path.basename(file_to_transcribe), f, "audio/wav")}
                resp = await client.post(API_FILE_ENDPOINT, files=files)

            # Clean up the temporary file if one was created
            if temp_file_to_delete:
                try:
                    os.remove(temp_file_to_delete)
                except Exception as e:
                    print(f"Could not delete temp file {temp_file_to_delete}: {e}")

            resp.raise_for_status()
            result = resp.json()
            transcript, duration = result.get("text", ""), result.get("duration", 0)
            processing_time = time.time() - start_time
    except httpx.RequestError as e:
        error_message = f"API request failed: {e}"
    except Exception as e:
        error_message = f"Unexpected error: {e}"

    return transcript, duration, processing_time, error_message


async def transcribe_ws(audio_file_path: str):
    """Gửi file wav qua WebSocket để transcribe theo chunk"""
    transcript = ""
    error_message = ""
    try:
        async with websockets.connect(WS_ENDPOINT, max_size=10 * 1024 * 1024) as ws:
            audio, sr = sf.read(audio_file_path)
            if len(audio.shape) > 1:  # stereo -> mono
                audio = np.mean(audio, axis=1)

            chunk_size = sr * 2  # 2s chunk
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i + chunk_size]
                buf = io.BytesIO()
                sf.write(buf, chunk, sr, format="WAV")
                buf.seek(0)
                await ws.send(buf.read())

                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    transcript = data.get("partial", transcript)
                except asyncio.TimeoutError:
                    pass

            await ws.close()
    except Exception as e:
        error_message = f"WebSocket error: {e}"

    return transcript, error_message
