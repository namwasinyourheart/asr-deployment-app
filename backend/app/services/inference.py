import time
import os
import sys

import torch

from app.core.config import settings
from faster_whisper import WhisperModel
from .enhance_speech import enhance_speech, _df_model, _df_state
from .postprocess_text import postprocess_text, _sec_dict, _cpr_model
from .audio_utils import load_audio, compute_duration

from .service_utils import setup_logger

logger = setup_logger(__name__)

CPR_MODEL_PATH = settings.CPR_MODEL_PATH
CPR_VOCAB_PATH = os.path.join(CPR_MODEL_PATH, "vocabulary")
sys.path.append(os.path.join(CPR_MODEL_PATH))


_model = None
_processor = None


MODEL_BACKEND = settings.MODEL_BACKEND

_vad_utils = None
_vad_model = None



def _ensure_vad_model():
    global _vad_model, _vad_utils
    if _vad_model is None:
        _vad_model, _vad_utils = torch.hub.load(
            # repo_or_dir="snakers4/silero-vad",
            repo_or_dir=settings.VAD_MODEL_PATH,
            model="silero_vad",
            source="local",
            force_reload=False
        )

def _load_faster_whisper_model():
    """
    Load faster-whisper model.
    """
    try:
        model_path = settings.WHISPER_CT2_MODEL_PATH
        logger.info("Loading faster-whisper model: %s", model_path)


        model = WhisperModel(
            model_path,
            device=settings.DEVICE,
            # device="cpu",
            compute_type="float16" if settings.DEVICE == "cuda" else "int8",
            # compute_type="int8"
        )
        return model
    except Exception as e:
        logger.exception("Failed to load faster-whisper model: %s", e)
        raise


def _load_transformers_whisper_model():
    try:
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
        from peft import PeftModel

        model_name = settings.WHISPER_HF_MODEL_PATH  # ví dụ: "openai/whisper-small"
        logger.info("Loading HF Whisper model: %s", model_name)

        processor = WhisperProcessor.from_pretrained(model_name)
        model = WhisperForConditionalGeneration.from_pretrained(model_name, load_in_8bit=settings.LOAD_IN_8BIT)

        model.generation_config.language = "vi"
        model.generation_config.task = "transcribe"

        # Nếu có adapter_path trong config thì merge adapter LoRA
        adapter_paths = settings.ADAPTER_PATHS
        adapter_paths = [p.strip() for p in adapter_paths.split(",") if p.strip()]

        if adapter_paths:
            try:
                logger.info("Merging adapters...")
                if isinstance(adapter_paths, str):
                    adapter_paths = [adapter_paths]  # convert to list if single path

                for path in adapter_paths:
                    model = PeftModel.from_pretrained(model, path)
                    model = model.merge_and_unload()
            except Exception as e:
                logger.exception("Failed to merge LoRA adapter: %s", e)
        # print("settings.LOAD_IN_8BIT:", settings.LOAD_IN_8BIT)

        if not settings.LOAD_IN_8BIT:
            if settings.DEVICE == "cuda" and torch.cuda.is_available():
                model = model.to("cuda")
            else:
                model = model.to("cpu")

        return model, processor
    except Exception as e:
        logger.exception("Failed to load Whisper model: %s", e)
        raise



def _ensure_whisper_model():
    global _model, _processor
    if _model is not None:
        return

    if MODEL_BACKEND == "faster_whisper":
        _model = _load_faster_whisper_model()
        _processor = None
        
    elif MODEL_BACKEND == "transformers":
        _model, _processor = _load_transformers_whisper_model()

def get_transcript(
    model, 
    processor, 
    audio_path: str,  
    model_backend: str="faster_whisper",
    beam_size: int=5,
    language: str="vi"
):
    logger.info("Getting transcript...")
    if model_backend == "faster_whisper":
        segments, info = model.transcribe(audio_path, beam_size=beam_size, language=language)
        text = " ".join([seg.text for seg in segments]).strip()
    
    elif model_backend == "transformers":
        audio_array, sr = load_audio(audio_path)


        inputs = processor(audio_array, sampling_rate=sr, return_tensors="pt")

        input_features = inputs.input_features

        input_features = input_features.to(model.device, dtype=model.dtype)

        with torch.no_grad():
            predicted_ids = model.generate(input_features, return_timestamps=True)

        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
        text = transcription[0] if transcription else ""

        logger.info("Transcript: %s", text)

    return text
        


def has_speech(audio_array, sr, min_speech_duration_ms=250):
    """
    Check if the audio has speech.
    audio_array: numpy 1D or torch.Tensor 1D
    """
    get_speech_timestamps = _vad_utils[0]

    if not isinstance(audio_array, torch.Tensor):
        wav_tensor = torch.from_numpy(audio_array).float()
    else:
        wav_tensor = audio_array.float()

    wav_tensor = wav_tensor.squeeze()

    # VAD
    speech_timestamps = get_speech_timestamps(
        wav_tensor,
        _vad_model,
        sampling_rate=sr,
        min_speech_duration_ms=min_speech_duration_ms
    )

    return len(speech_timestamps) > 0


def asr_infer(
    audio_path: str,
    do_enhance_speech: bool = False,
    do_postprocess_text: bool = True,
    milliseconds: bool = True
) -> dict:
    """
    Run inference with faster-whisper.
    Return dict {"text": ..., "duration": ..., "processing_time": ...}
    Duration is in seconds or milliseconds depending on the flag.
    """
    _ensure_vad_model()
    _ensure_whisper_model()

    # print("MODEL_BACKEND:", MODEL_BACKEND)
    if MODEL_BACKEND:
        logger.info(
            "Running inference on %s with backend %s",
            audio_path,
            MODEL_BACKEND
        )

        total_processing_start = time.time()

        audio_array, sr = load_audio(audio_path)
        duration = compute_duration(audio_array, sr, milliseconds=milliseconds)

        # Check if audio has speech
        if not has_speech(audio_array, sr):
            total_processing_time = time.time() - total_processing_start
            if milliseconds:
                total_processing_time = round(total_processing_time * 1000, 3)
            else:
                total_processing_time = round(total_processing_time, 3)
            logger.info("No speech detected in audio: %s", audio_path)
            
            return {
                "text": "",
                "duration": duration,
                "total_processing_time": total_processing_time,
                "speech_enhancement_time": None,
                "asr_time": None,
                "text_postprocessing_time": None,
            }


        # Speech Enhancement
        if do_enhance_speech:
            speech_enhancement_start = time.time()
            enhanced_path = os.path.splitext(audio_path)[0] + "_enhanced.wav"

            try:
                enhance_speech(
                    model=_df_model,
                    df_state=_df_state,
                    input_wav=audio_path,
                    output_wav=enhanced_path,
                    device=settings.DEVICE,
                )
                audio_path = enhanced_path  # dùng file đã enhance cho ASR
                logger.info("Speech enhancement done: %s", enhanced_path)
            except Exception as e:
                logger.exception("Speech enhancement failed: %s", e)

            speech_enhancement_time = time.time() - speech_enhancement_start
            
            if milliseconds:
                speech_enhancement_time = round(speech_enhancement_time * 1000, 3)
            else:
                speech_enhancement_time = round(speech_enhancement_time, 3)
        else:
            speech_enhancement_time = None


        # Transcribe
        asr_start = time.time()

        text = get_transcript(_model, _processor, audio_path, model_backend=MODEL_BACKEND, beam_size=5, language="vi")

        asr_time = time.time() - asr_start
        if milliseconds:
            asr_time = round(asr_time * 1000, 3)
        else:
            asr_time = round(asr_time, 3)

        logger.info("Raw Transcript: %s", text)


        # Postprocess Text
        if do_postprocess_text:
            text_postprocessing_start = time.time()
            postprocessed_text = postprocess_text(text, _sec_dict, _cpr_model)
            postprocessed_text = postprocessed_text["text"]


            # if isinstance(postprocessed_text, list):
            #     postprocessed_text = postprocessed_text[0]
            text = postprocessed_text
            logger.info("Postprocessed Transcript: %s", text)
            text_postprocessing_time = time.time() - text_postprocessing_start

        else:
            text_postprocessing_time = None

        # Total Processing Time
        if text_postprocessing_time:
            if milliseconds:
                text_postprocessing_time = round(text_postprocessing_time * 1000, 3)
            else:
                text_postprocessing_time = round(text_postprocessing_time, 3)
            

        total_processing_time = time.time() - total_processing_start
        if milliseconds:
            total_processing_time = round(total_processing_time * 1000, 3)
        else:
            total_processing_time = round(total_processing_time, 3)

        if milliseconds:
            logger.info(
                f"Transcript: %s | Duration: %s ms | ASR Time: %s ms | Text Postprocessing Time: %s ms | Total Processing Time: %s ms",
                text,
                duration,
                asr_time,
                text_postprocessing_time,
                total_processing_time,
            )
        else:
            logger.info(
                f"Transcript: %s | Duration: %s s | ASR Time: %s s | Text Postprocessing Time: %s s | Total Processing Time: %s s",
                text,
                duration,
                asr_time,
                text_postprocessing_time,
                total_processing_time,
            )


        # Cleanup temporary enhanced file
        if do_enhance_speech and enhanced_path and os.path.exists(enhanced_path):
            try:
                os.remove(enhanced_path)
                logger.info("Removed temporary enhanced file: %s", enhanced_path)
            except Exception as e:
                logger.warning("Could not remove enhanced file %s: %s", enhanced_path, e)


        return {
            "text": text,
            "duration": duration,
            "total_processing_time": total_processing_time,
            "speech_enhancement_time": None,
            "asr_time": asr_time,
            "text_postprocessing_time": text_postprocessing_time,
        }

    else:
        return {
            "text": "",
            "duration": None,
            "total_processing_time": None,
            "speech_enhancement_time": None,
            "asr_time": None,
            "text_postprocessing_time": None,
        }

