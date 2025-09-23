import gradio as gr
import requests
import os
import time
import tempfile
import shutil

# --- Các hằng số và hàm tiện ích (không đổi) ---
API_FILE_ENDPOINT = "http://127.0.0.1:8000/api/v1/asr/file"
API_URL_ENDPOINT = "http://127.0.0.1:8000/api/v1/asr/url"

def download_audio_from_url(url):
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return None, "Invalid URL provided."
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
            with requests.get(url, stream=True, timeout=20) as r:
                r.raise_for_status()
                shutil.copyfileobj(r.raw, fp)
            return fp.name, None
    except requests.exceptions.RequestException as e:
        return None, f"Failed to download audio: {e}"
    except Exception as e:
        return None, f"An error occurred: {e}"

# --- Hàm logic chính (không đổi) ---
def generate_transcribe(audio_source, audio_file_or_url):
    transcript, duration, processing_time, error_message = "", 0, 0, ""
    if audio_source == "URL":
        try:
            start_time = time.time()
            resp = requests.post(
                API_URL_ENDPOINT, data={"audio_url": audio_file_or_url},
                headers={"accept": "application/json"}, timeout=60
            )
            resp.raise_for_status()
            result = resp.json()
            transcript, duration = result.get("text", ""), result.get("duration", 0)
            processing_time = time.time() - start_time
        except requests.exceptions.RequestException as e:
            error_message = f"API request failed: {e}"
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
    else:
        try:
            start_time = time.time()
            with open(audio_file_or_url, "rb") as f:
                files = {"audio_file": (os.path.basename(audio_file_or_url), f, "audio/wav")}
                resp = requests.post(
                    API_FILE_ENDPOINT, files=files,
                    headers={"accept": "application/json"}, timeout=120
                )
            resp.raise_for_status()
            result = resp.json()
            transcript, duration = result.get("text", ""), result.get("duration", 0)
            processing_time = time.time() - start_time
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"

    if error_message:
        return "", "", "", error_message, gr.update(visible=True)
    else:
        return transcript, f"{duration:.2f}s", f"{processing_time:.2f}s", "", gr.update(visible=False)

# --- Bố cục Gradio ---
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

            # "Your Audio" chỉ dùng cho File và URL
            audio_waveform_display = gr.Audio(label="Your Audio", visible=False, interactive=False)
            transcribe_button = gr.Button("Transcribe Audio")

        with gr.Column():
            gr.Markdown("## Transcription Results")
            output_transcript = gr.Textbox(label="Transcript", lines=10)
            output_duration = gr.Textbox(label="Audio Duration")
            output_processing_time = gr.Textbox(label="Processing Time")
            output_error = gr.Textbox(label="Error", visible=False, interactive=False, container=False)

    # --- Logic điều khiển giao diện và trạng thái ---

    def update_ui_on_tab_change(choice, current_state):
        show_mic = gr.update(visible=(choice == "Microphone"))
        show_file = gr.update(visible=(choice == "File"))
        show_url = gr.update(visible=(choice == "URL"))

        # *** THAY ĐỔI QUAN TRỌNG ***
        # Nếu là tab Microphone, luôn ẩn waveform phụ
        if choice == "Microphone":
            waveform_update = gr.update(value=None, visible=False)
        else:
            # Đối với File và URL, hiển thị waveform nếu có
            audio_info_for_current_tab = current_state.get(choice, {})
            local_path = audio_info_for_current_tab.get("local_path")
            if local_path:
                waveform_update = gr.update(value=local_path, visible=True)
            else:
                waveform_update = gr.update(value=None, visible=False)
            
        return show_mic, show_file, show_url, waveform_update

    def cache_mic_audio(audio_path, current_state):
        """*** THAY ĐỔI QUAN TRỌNG ***
        Chỉ cập nhật state cho Microphone, không trả về update cho UI.
        """
        if not audio_path:
            current_state["Microphone"] = {"source_data": None, "local_path": None}
        else:
            current_state["Microphone"] = {"source_data": audio_path, "local_path": audio_path}
        return current_state
        
    def cache_file_audio(audio_path, current_state):
        """Cache audio từ File và hiển thị waveform."""
        if not audio_path:
            current_state["File"] = {"source_data": None, "local_path": None}
            return gr.update(visible=False, value=None), current_state
        
        current_state["File"] = {"source_data": audio_path.name, "local_path": audio_path.name}
        return gr.update(value=audio_path.name, visible=True), current_state

    def cache_url_audio(url, current_state):
        """Tải, cache audio từ URL và hiển thị waveform."""
        local_path, error = download_audio_from_url(url)
        if error:
            current_state["URL"] = {"source_data": url, "local_path": None} # Cập nhật state dù lỗi
            return gr.update(visible=False), current_state, error, gr.update(visible=True)
        
        current_state["URL"] = {"source_data": url, "local_path": local_path}
        return gr.update(value=local_path, visible=True), current_state, "", gr.update(visible=False)

    def process_transcription(active_tab, current_state):
        audio_info = current_state.get(active_tab, {})
        source_data = audio_info.get("source_data")
        if not source_data:
            return "", "", "", f"Please provide an audio source in the '{active_tab}' tab first.", gr.update(visible=True)
        return generate_transcribe(active_tab, source_data)

    # --- Gán sự kiện cho các thành phần ---
    
    audio_source_radio.change(
        fn=update_ui_on_tab_change,
        inputs=[audio_source_radio, all_cached_audio_info],
        outputs=[microphone_input, file_input, url_group, audio_waveform_display],
        queue=False
    )
    
    # *** THAY ĐỔI QUAN TRỌNG ***
    microphone_input.stop_recording(
        fn=cache_mic_audio,
        inputs=[microphone_input, all_cached_audio_info],
        outputs=[all_cached_audio_info] # Chỉ cập nhật state
    )
    microphone_input.clear(
        lambda s: cache_mic_audio(None, s),
        inputs=[all_cached_audio_info],
        outputs=[all_cached_audio_info] # Chỉ cập nhật state
    )
    
    file_input.upload(
        fn=cache_file_audio,
        inputs=[file_input, all_cached_audio_info],
        outputs=[audio_waveform_display, all_cached_audio_info]
    )
    file_input.clear(
        # Hàm lambda phức tạp hơn một chút vì cache_file_audio trả về 2 giá trị
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
        fn=process_transcription,
        inputs=[audio_source_radio, all_cached_audio_info],
        outputs=[output_transcript, output_duration, output_processing_time, output_error, output_error]
    )

demo.launch(share=True)