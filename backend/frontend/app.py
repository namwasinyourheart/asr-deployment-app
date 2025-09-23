# frontend_streaming_upload_url_fixed.py
import gradio as gr
import numpy as np
import websocket
import threading
import io
import json
import time
import soundfile as sf
import requests

# ---------------- WebSocket client for mic streaming ----------------
class ASRWebSocket:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self._running = False
        self._lock = threading.Lock()
        self.connect()

    def connect(self):
        try:
            self.ws = websocket.create_connection(self.url, timeout=5)
            self._running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
        except Exception as e:
            print(f"Failed to connect to WebSocket: {e}")
            self._running = False

    def _receive_loop(self):
        global current_transcript
        try:
            while self._running:
                msg = self.ws.recv()
                if not msg:
                    continue
                try:
                    data = json.loads(msg)
                    current_transcript = data.get("partial", "")
                except json.JSONDecodeError:
                    current_transcript = msg
        except Exception as e:
            print(f"Receive loop error: {e}")
            self._running = False

    def send_chunk(self, audio_chunk: np.ndarray, sr: int = 16000):
        buf = io.BytesIO()
        sf.write(buf, audio_chunk, sr, format="WAV")
        buf.seek(0)
        with self._lock:
            if not self._running:
                self.connect()
            try:
                self.ws.send_binary(buf.read())
            except Exception as e:
                print(f"Send chunk failed: {e}")
                self._running = False
                self.connect()

    def close(self):
        self._running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

# ---------------- Global variables ----------------
WS_URL = "ws://localhost:8000/api/v1/asr/chunk"
asr_client = None
current_transcript = ""
buffer = np.zeros((0,), dtype=np.float32)

def ensure_client():
    global asr_client
    if asr_client is None or not asr_client._running:
        if asr_client:
            asr_client.close()
        asr_client = ASRWebSocket(WS_URL)

# ---------------- Gradio callbacks ----------------
def stream_callback(frame, sr):
    global buffer
    if frame is None:
        return current_transcript
    ensure_client()
    arr = np.asarray(frame)
    if arr.ndim > 1:
        arr = arr[:,0]
    buffer = np.concatenate([buffer, arr])

    CHUNK_SIZE = 32000  # ~2s
    while len(buffer) >= CHUNK_SIZE:
        chunk = buffer[:CHUNK_SIZE]
        buffer = buffer[CHUNK_SIZE:]
        asr_client.send_chunk(chunk, sr)
    return current_transcript

def stop_callback():
    global asr_client, current_transcript, buffer
    if asr_client:
        asr_client.close()
        asr_client = None   
    current_transcript = ""
    buffer = np.zeros((0,), dtype=np.float32)
    return "Stopped"

def upload_file_callback(audio_file):
    if audio_file is None:
        return ""
    sr, arr = audio_file
    if arr.ndim > 1:
        arr = arr[:,0]
    with io.BytesIO() as buf:
        sf.write(buf, arr, sr, format="WAV")
        buf.seek(0)
        files = {"audio_file": ("file.wav", buf, "audio/wav")}
        import requests
        r = requests.post("http://localhost:8000/api/v1/asr/file", files=files)
        if r.status_code == 200:
            return r.json().get("text", "")
        else:
            return f"Error: {r.text}"

def url_callback(audio_url):
    import requests
    if not audio_url.startswith("http"):
        return "Invalid URL"
    r = requests.post("http://localhost:8000/api/v1/asr/url", data={"audio_url": audio_url})
    if r.status_code == 200:
        return r.json().get("text", "")
    else:
        return f"Error: {r.text}"

# ---------------- Gradio interface ----------------
with gr.Blocks() as demo:
    gr.Markdown("## Whisper ASR: Mic streaming + Upload file + URL")

    with gr.Tab("Mic streaming"):
        mic = gr.Audio(sources=["microphone"], type="numpy", streaming=True, label="Mic input")
        transcript_mic = gr.Textbox(label="Transcript", interactive=False)
        stop_btn = gr.Button("Stop")
        mic.stream(stream_callback, outputs=transcript_mic)
        stop_btn.click(stop_callback, outputs=transcript_mic)

    with gr.Tab("Upload file"):
        upload_audio = gr.Audio(sources=["upload"], type="numpy", label="Upload audio")
        transcript_upload = gr.Textbox(label="Transcript", interactive=False)
        upload_btn = gr.Button("Transcribe")
        upload_btn.click(upload_file_callback, inputs=upload_audio, outputs=transcript_upload)

    with gr.Tab("Audio URL"):
        url_input = gr.Textbox(label="Audio URL")
        transcript_url = gr.Textbox(label="Transcript", interactive=False)
        url_btn = gr.Button("Transcribe")
        url_btn.click(url_callback, inputs=url_input, outputs=transcript_url)

if __name__ == "__main__":
    demo.launch()
