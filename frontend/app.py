import gradio as gr
import httpx
import os
import time
import tempfile
import shutil

API_FILE_ENDPOINT = "http://127.0.0.1:8000/api/v1/asr/file"
API_URL_ENDPOINT = "http://127.0.0.1:8000/api/v1/asr/url"

# --- Utility functions ---
# def download_audio_from_url(url):
#     if not url or not (url.startswith("http://") or url.startswith("https://")):
#         return None, "Invalid URL provided."
#     try:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
#             with httpx.stream("GET", url, timeout=20) as r:
#                 r.raise_for_status()
#                 shutil.copyfileobj(r, fp)
#             return fp.name, None
#     except Exception as e:
#         return None, f"Failed to download audio: {e}"

def download_audio_from_url(url):
    try:
        # Tạo file tạm
        output_path = tempfile.mktemp(suffix=".wav")

        # Dùng client để follow redirect
        with httpx.Client(follow_redirects=True, timeout=60) as client:
            r = client.get(url)
            # Nếu file lớn, Google sẽ trả HTML với confirm token
            if "drive.google.com" in r.url.host and "export=download" in r.url.query:
                m = re.search(r"confirm=([0-9A-Za-z_]+)", r.text)
                if m:
                    token = m.group(1)
                    download_url = url + "&confirm=" + token
                    r = client.get(download_url)
            r.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(r.content)
        return output_path, None

    except Exception as e:
        return None, f"Failed to download audio: {e}"


# --- Async transcription function ---
async def generate_transcribe_async(audio_source, audio_file_or_url):
    transcript, duration, processing_time, error_message = "", 0, 0, ""
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            if audio_source == "URL":
                resp = await client.post(API_URL_ENDPOINT, data={"audio_url": audio_file_or_url})
            else:
                f = open(audio_file_or_url, "rb")
                files = {"audio_file": (os.path.basename(audio_file_or_url), f, "audio/wav")}
                resp = await client.post(API_FILE_ENDPOINT, files=files)
                f.close()
            resp.raise_for_status()
            result = resp.json()
            transcript, duration = result.get("text", ""), result.get("duration", 0)
            processing_time = time.time() - start_time
    except httpx.RequestError as e:
        error_message = f"API request failed: {e}"
    except Exception as e:
        error_message = f"Unexpected error: {e}"

    if error_message:
        return "", "", "", error_message, gr.update(visible=True)
    else:
        return transcript, f"{duration:.2f}s", f"{processing_time:.2f}s", "", gr.update(visible=False)


# --- Async wrapper for Gradio ---
async def process_transcription_async(active_tab, current_state):
    audio_info = current_state.get(active_tab, {})
    source_data = audio_info.get("source_data")
    if not source_data:
        return "", "", "", f"Please provide an audio source in the '{active_tab}' tab first.", gr.update(visible=True)
    return await generate_transcribe_async(active_tab, source_data)


import asyncio
import websockets
import json
import soundfile as sf
import io
import numpy as np

WS_ENDPOINT = "ws://127.0.0.1:8000/api/v1/asr/chunk"

async def generate_transcribe_ws(audio_source, audio_file_or_path):
    """
    audio_source: "Microphone" | "File" | "URL"
    audio_file_or_path: đường dẫn file WAV hoặc tạm file tải từ URL
    """
    transcript = ""
    error_message = ""
    try:
        async with websockets.connect(WS_ENDPOINT, max_size=10*1024*1024) as ws:
            # Nếu audio là mic/file: đọc file WAV
            audio, sr = sf.read(audio_file_or_path)

            # Chia chunk 2 giây
            chunk_size = sr * 2
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i+chunk_size]
                buf = io.BytesIO()
                sf.write(buf, chunk, sr, format="WAV")
                buf.seek(0)
                await ws.send(buf.read())

                # Nhận partial transcript từ server
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    transcript = data.get("partial", transcript)
                except asyncio.TimeoutError:
                    pass  # không sao, tiếp tục gửi chunk

            # Gửi EOF nếu server yêu cầu (tùy implement)
            # await ws.send(b"EOS")
            await ws.close()
    except Exception as e:
        error_message = f"WebSocket error: {e}"

    return transcript, error_message


async def process_transcription_ws(active_tab, current_state):
    audio_info = current_state.get(active_tab, {})
    source_path = audio_info.get("local_path")
    if not source_path:
        return "", f"Please provide an audio source in the '{active_tab}' tab.", gr.update(visible=True)
    transcript, error = await generate_transcribe_ws(active_tab, source_path)
    if error:
        return "", error, gr.update(visible=True)
    return transcript, "", gr.update(visible=False)



# --- Gradio UI ---
with gr.Blocks(css="footer {display: none !important}") as demo:
    all_cached_audio_info = gr.State({
        "Microphone": {"source_data": None, "local_path": None},
        "File":       {"source_data": None, "local_path": None},
        "URL":        {"source_data": None, "local_path": None}
    })

    gr.Markdown("# 🎤 ASR Application")
    with gr.Row():
        with gr.Column():
            gr.Markdown("## Get Audio")
            audio_source_radio = gr.Radio(
                ["Microphone", "File", "URL"],
                label="Select Audio Source", value="Microphone"
            )

            microphone_input = gr.Audio(sources=["microphone"], type="filepath", label="Record from Microphone", visible=True)
            file_input = gr.File(file_types=[".mp3", ".wav", ".flac"], label="Upload Audio File", visible=False)
            with gr.Group(visible=False) as url_group:
                url_input = gr.Textbox(label="Audio URL", placeholder="Enter URL of audio file...")
                url_load_button = gr.Button("Load Audio")

            audio_waveform_display = gr.Audio(label="Your Audio", visible=False, interactive=False)
            transcribe_button = gr.Button("Transcribe Audio")

        with gr.Column():
            gr.Markdown("## Transcription Results")
            output_transcript = gr.Textbox(label="Transcript", lines=10)
            output_duration = gr.Textbox(label="Audio Duration")
            output_processing_time = gr.Textbox(label="Processing Time")
            output_error = gr.Textbox(label="Error", visible=False, interactive=False, container=False)

    # --- UI logic ---
    def update_ui_on_tab_change(choice, current_state):
        show_mic = gr.update(visible=(choice == "Microphone"))
        show_file = gr.update(visible=(choice == "File"))
        show_url = gr.update(visible=(choice == "URL"))

        if choice == "Microphone":
            waveform_update = gr.update(value=None, visible=False)
        else:
            audio_info_for_current_tab = current_state.get(choice, {})
            local_path = audio_info_for_current_tab.get("local_path")
            if local_path:
                waveform_update = gr.update(value=local_path, visible=True)
            else:
                waveform_update = gr.update(value=None, visible=False)
            
        return show_mic, show_file, show_url, waveform_update

    def cache_mic_audio(audio_path, current_state):
        if not audio_path:
            current_state["Microphone"] = {"source_data": None, "local_path": None}
        else:
            current_state["Microphone"] = {"source_data": audio_path, "local_path": audio_path}
        return current_state
        
    def cache_file_audio(audio_path, current_state):
        if not audio_path:
            current_state["File"] = {"source_data": None, "local_path": None}
            return gr.update(visible=False, value=None), current_state
        
        current_state["File"] = {"source_data": audio_path.name, "local_path": audio_path.name}
        return gr.update(value=audio_path.name, visible=True), current_state

    def cache_url_audio(url, current_state):
        local_path, error = download_audio_from_url(url)
        if error:
            current_state["URL"] = {"source_data": url, "local_path": None}
            return gr.update(visible=False), current_state, error, gr.update(visible=True)
        current_state["URL"] = {"source_data": url, "local_path": local_path}
        return gr.update(value=local_path, visible=True), current_state, "", gr.update(visible=False)

    # --- Connect events ---
    audio_source_radio.change(
        fn=update_ui_on_tab_change,
        inputs=[audio_source_radio, all_cached_audio_info],
        outputs=[microphone_input, file_input, url_group, audio_waveform_display],
        queue=False
    )
    
    microphone_input.stop_recording(
        fn=cache_mic_audio,
        inputs=[microphone_input, all_cached_audio_info],
        outputs=[all_cached_audio_info]
    )
    microphone_input.clear(
        lambda s: cache_mic_audio(None, s),
        inputs=[all_cached_audio_info],
        outputs=[all_cached_audio_info]
    )
    
    file_input.upload(
        fn=cache_file_audio,
        inputs=[file_input, all_cached_audio_info],
        outputs=[audio_waveform_display, all_cached_audio_info]
    )
    file_input.clear(
        lambda s: (gr.update(value=None, visible=False), cache_file_audio(None, s)[1]),
        inputs=[all_cached_audio_info],
        outputs=[audio_waveform_display, all_cached_audio_info]
    )
    
    url_load_button.click(
        fn=cache_url_audio,
        inputs=[url_input, all_cached_audio_info],
        outputs=[audio_waveform_display, all_cached_audio_info, output_error, output_error]
    )
    
    transcribe_button.click(
        fn=process_transcription_async,
        inputs=[audio_source_radio, all_cached_audio_info],
        outputs=[output_transcript, output_duration, output_processing_time, output_error, output_error]
    )

#     transcribe_button.click(
#         fn=process_transcription_ws,
#         inputs=[audio_source_radio, all_cached_audio_info],
#         outputs=[output_transcript, output_error, output_error]
# )


# --- Launch Gradio với queue để hỗ trợ request đồng thời ---
demo.launch(share=True)
