import asyncio
import gradio as gr
import numpy as np
import soundfile as sf
from audiomentations import TimeStretch, Compose
from utils import download_audio_from_url, save_corrections
from api_client import transcribe_async, transcribe_ws

def apply_speedup(audio_path, speed_rate, return_path_only=False):
    """
    Apply speedup to audio and return either a Gradio update object or the file path
    
    Args:
        audio_path: Path to the input audio file
        speed_rate: Speed multiplier (1.0 = normal speed)
        return_path_only: If True, returns only the path to the processed audio
    """
    if not audio_path or speed_rate == 1.0:
        return audio_path if return_path_only else gr.update(visible=False)
        
    try:
        # Load audio
        audio, sr = sf.read(audio_path)
        
        # Apply speedup
        speedup_effect = Compose([
            TimeStretch(
                min_rate=speed_rate, 
                max_rate=speed_rate, 
                p=1.0, 
                leave_length_unchanged=False
            )
        ])
        audio_speedup = speedup_effect(audio, sr)
        
        # Save to temp file
        import tempfile
        temp_path = tempfile.mktemp(suffix='.wav')
        sf.write(temp_path, audio_speedup, sr)
        
        return temp_path if return_path_only else gr.update(
            value=temp_path, 
            visible=True, 
            label=f"Tốc độ phát x{speed_rate:.1f}"
        )
    except Exception as e:
        print(f"Error applying speedup: {e}")
        return gr.update(visible=False)

# --- Async transcription wrapper ---
async def process_transcription_async(active_tab, current_state, speedup_rate=1.0):
    audio_info = current_state.get(active_tab, {})
    source_data = audio_info.get("source_data")
    if not source_data:
        return "", "", "", f"Please provide an audio source in the '{active_tab}' tab first.", gr.update(visible=True)

    # If speedup is applied, use the speedup audio path for any tab
    if speedup_rate != 1.0 and audio_info.get("local_path"):
        try:
            # Create a temporary file with speedup
            temp_path = await asyncio.to_thread(
                apply_speedup, 
                audio_info["local_path"], 
                speedup_rate,
                True  # Return path only
            )
            if temp_path:  # If we got a valid path
                source_data = temp_path
                print(f"Using speedup audio at {speedup_rate}x: {source_data}")
        except Exception as e:
            print(f"Error applying speedup for transcription: {e}")

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
                    with gr.Row():
                        url_load_button = gr.Button("Load Audio", variant="primary")
                    audio_player = gr.Audio(visible=False, label="Loaded Audio")
                    
                with gr.Row(visible=True) as speedup_group:
                    with gr.Column():
                        gr.Markdown("### Tốc độ phát")
                        speedup_slider = gr.Slider(
                            minimum=0.5,
                            maximum=3.0,
                            value=1.0,
                            step=0.1,
                            label="Tốc độ phát (1.0 = bình thường)",
                            interactive=True
                        )
                        speedup_audio = gr.Audio(visible=False, label="Âm thanh đã điều chỉnh tốc độ")

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
            
            # Show speedup controls for all tabs
            show_speedup = gr.update(visible=True)

            return show_mic, show_file, show_url, show_speedup

        def cache_mic_audio(audio_path, current_state):
            current_state["Microphone"] = {"source_data": audio_path, "local_path": audio_path}
            return current_state
        
        def cache_file_audio(audio_path, current_state):
            if not audio_path:
                current_state["File"] = {"source_data": None, "local_path": None}
                return current_state
            current_state["File"] = {"source_data": audio_path.name, "local_path": audio_path.name}
            return current_state

        def cache_url_audio(url, current_state):
            local_path, error = download_audio_from_url(url)
            if error:
                current_state["URL"] = {"source_data": url, "local_path": None}
                return current_state, error, gr.update(visible=True)
            current_state["URL"] = {"source_data": url, "local_path": local_path}
            return current_state, "", gr.update(visible=False)

        # --- Connect events ---
        audio_source_radio.change(
            fn=update_ui_on_tab_change,
            inputs=[audio_source_radio, all_cached_audio_info],
            outputs=[microphone_input, file_input, url_group, speedup_group],
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
            outputs=[all_cached_audio_info]
        )
                
        def handle_url_load(url, current_state, speed_rate):
            if not url:
                return (
                    current_state, 
                    "Vui lòng nhập URL", 
                    gr.update(visible=True), 
                    gr.update(visible=False),
                    gr.update(visible=False)
                )
                
            result = cache_url_audio(url, current_state)
            if len(result) == 3:  # If cache_url_audio returns 3 values
                current_state, error, error_visible = result
                if error:
                    return (
                        current_state, 
                        error, 
                        gr.update(visible=True, value=error), 
                        gr.update(visible=False),
                        gr.update(visible=False)
                    )
                
                # Show original audio
                audio_update = gr.update(value=result[0]["URL"]["local_path"], visible=True)
                
                # Apply speedup if needed (default to 1.0x on initial load)
                speedup_update = apply_speedup(result[0]["URL"]["local_path"], 1.0)
                
                return (
                    current_state, 
                    "Tải file âm thanh thành công!", 
                    gr.update(visible=False), 
                    audio_update,
                    speedup_update
                )
            else:  # Fallback in case cache_url_audio changes
                return (
                    result[0], 
                    "Tải file âm thanh thành công!", 
                    gr.update(visible=False), 
                    gr.update(visible=False),
                    gr.update(visible=False)
                )
            
        # Toggle speedup preview when checkbox changes
        def on_speedup_change(speed_rate, current_state, active_tab):
            if not current_state.get(active_tab, {}).get("local_path"):
                return gr.update(visible=False)
            return apply_speedup(current_state[active_tab]["local_path"], speed_rate)
            
        speedup_slider.release(
            fn=on_speedup_change,
            inputs=[speedup_slider, all_cached_audio_info, audio_source_radio],
            outputs=[speedup_audio]
        )
        
        url_load_button.click(
            fn=handle_url_load,
            inputs=[
                url_input, 
                all_cached_audio_info,
                gr.State(1.0)  # Default speed rate (1.0x = normal speed)
            ],
            outputs=[
                all_cached_audio_info, 
                output_error, 
                output_error, 
                audio_player,
                speedup_audio
            ]
        )
        transcribe_button.click(
            fn=process_transcription_async,
            inputs=[
                audio_source_radio, 
                all_cached_audio_info,
                speedup_slider  # Pass the speedup rate to the transcription function
            ],
            outputs=[output_transcript, output_duration, output_processing_time, output_error, output_error]
        )

        # save_button.click(
        #     fn=save_corrections,
        #     inputs=[user_name_input, corrections_input],
        #     outputs=[save_status]
        # )

    return demo
