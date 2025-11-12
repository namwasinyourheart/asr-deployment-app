import gradio as gr
from utils import download_audio_from_url, save_corrections
from api_client import transcribe_async, transcribe_ws

# --- Async transcription wrapper ---
async def process_transcription_async(active_tab, current_state):
    audio_info = current_state.get(active_tab, {})
    source_data = audio_info.get("source_data")
    if not source_data:
        return "", "", "", f"Please provide an audio source in the '{active_tab}' tab first.", gr.update(visible=True)

    transcript, duration, processing_time, error = await transcribe_async(active_tab, source_data)
    if error:
        return "", "", "", error, gr.update(visible=True)
    return transcript, f"{duration:.2f}s", f"{processing_time:.2f}s", "", gr.update(visible=False)


async def process_transcription_ws(active_tab, current_state):
    audio_info = current_state.get(active_tab, {})
    source_path = audio_info.get("local_path")
    if not source_path:
        return "", f"Please provide an audio source in the '{active_tab}' tab.", gr.update(visible=True)

    transcript, error = await transcribe_ws(source_path)
    if error:
        return "", error, gr.update(visible=True)
    return transcript, "", gr.update(visible=False)


# --- Build Gradio UI ---
def build_ui():
    with gr.Blocks(css="footer {display: none !important}") as demo:
        all_cached_audio_info = gr.State({
            "Microphone": {"source_data": None, "local_path": None},
            "File":       {"source_data": None, "local_path": None},
            "URL":        {"source_data": None, "local_path": None}
        })

        gr.Markdown("# 🎤 VnPost Speech-to-Text")
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


                # gr.Markdown("## Suggesting Corrections")
                # with gr.Accordion("Your Corrections", open=True):
                #     user_name_input = gr.Textbox(label="Your Name")
                #     corrections_input = gr.Textbox(
                #         label="Corrections (one per line)",
                #         placeholder="Example:\nhelo -> hello\nthsi -> this",
                #         lines=5
                #     )
                #     save_button = gr.Button("Save Corrections")
                    # save_status = gr.Markdown("")


        # --- UI logic ---
        def update_ui_on_tab_change(choice, current_state):
            show_mic = gr.update(visible=(choice == "Microphone"))
            show_file = gr.update(visible=(choice == "File"))
            show_url = gr.update(visible=(choice == "URL"))

            if choice == "Microphone":
                waveform_update = gr.update(value=None, visible=False)
            else:
                local_path = current_state.get(choice, {}).get("local_path")
                waveform_update = gr.update(value=local_path, visible=bool(local_path))
            return show_mic, show_file, show_url, waveform_update

        def cache_mic_audio(audio_path, current_state):
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
        file_input.upload(
            fn=cache_file_audio,
            inputs=[file_input, all_cached_audio_info],
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

        # save_button.click(
        #     fn=save_corrections,
        #     inputs=[user_name_input, corrections_input],
        #     outputs=[save_status]
        # )

    return demo
