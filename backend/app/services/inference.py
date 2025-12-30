import time
import os
import sys
import torch
from typing import Optional, Dict, Any

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


# Global cache for loaded models
_models_cache: Dict[str, Any] = {}
_processor = None
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

def _load_faster_whisper_model(model_name: Optional[str] = None):
    """
    Load faster-whisper model.
    
    Args:
        model_name: Name of the model to load. If None, uses default model.
    """
    cache_key = f"faster_whisper_{model_name or 'default'}"
    
    # Return cached model if available
    if cache_key in _models_cache:
        return _models_cache[cache_key]
        
    try:
        if model_name is None:
            # Backward compatibility
            model_path = settings.WHISPER_CT2_MODEL_PATH
            logger.info("Loading default faster-whisper model: %s", model_path)
            model = WhisperModel(
                model_path,
                device=settings.DEVICE,
                compute_type="float16" if settings.DEVICE == "cuda" else "int8",
            )
        else:
            # New model configuration system
            if settings.is_adapter_model(model_name):
                # Handle adapter-based model
                base_model = settings.get_base_model(model_name)
                adapter_path = settings.get_adapter_path(model_name)
                logger.info(f"Loading adapter-based model: {model_name} (base: {base_model}, adapter: {adapter_path})")
                model = WhisperModel(
                    base_model,
                    device=settings.DEVICE,
                    compute_type="float16" if settings.DEVICE == "cuda" else "int8",
                )
                # TODO: Add adapter loading logic here if needed
            else:
                # Handle single model file
                model_path = settings.get_base_model(model_name)
                logger.info(f"Loading model {model_name} from {model_path}")
                model = WhisperModel(
                    model_path,
                    device=settings.DEVICE,
                    compute_type="float16" if settings.DEVICE == "cuda" else "int8",
                )
        
        # Cache the loaded model
        _models_cache[cache_key] = model
        return model
        
    except Exception as e:
        logger.exception("Failed to load faster-whisper model: %s", e)
        raise


def _load_transformers_whisper_model(model_name: Optional[str] = None):
    """
    Load transformers Whisper model with optional LoRA adapter.
    
    Args:
        model_name: Name of the model to load. If None, uses default model.
    """
    try:
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
        from peft import PeftModel, PeftConfig
        import os

        # Get model configuration
        model_config = settings.get_model_config(model_name)
        
        # Handle both single model path and (base_model, adapter_path) tuple
        if isinstance(model_config, tuple):
            base_model, adapter_path = model_config
        else:
            base_model = model_config
            adapter_path = None
        
        logger.info(f"Loading HF Whisper model: {base_model}")
        # if adapter_path:
        #     logger.info(f"With adapter from: {adapter_path}")

        # Load base model and processor
        processor = WhisperProcessor.from_pretrained(base_model)
        model = WhisperForConditionalGeneration.from_pretrained(
            base_model,
            load_in_8bit=settings.LOAD_IN_8BIT,
            device_map="auto" if settings.DEVICE == "cuda" else None
        )

        # Configure generation
        model.generation_config.language = "vi"
        model.generation_config.task = "transcribe"

        # Load and merge adapter if specified
        if adapter_path and os.path.exists(adapter_path):
            logger.info(f"With adapter from: {adapter_path}")
            try:
                # Check if adapter config exists
                config_path = os.path.join(adapter_path, "adapter_config.json")
                if not os.path.exists(config_path):
                    raise FileNotFoundError(f"Adapter config not found at {config_path}")
                
                logger.info(f"Loading adapter from {adapter_path}")
                model = PeftModel.from_pretrained(model, adapter_path)
                model = model.merge_and_unload()
                logger.info("Successfully merged adapter")
                
            except Exception as e:
                logger.error(f"Failed to load adapter from {adapter_path}: {str(e)}")
                logger.info("Continuing with base model only...")
        
        # Skip moving model if using 8-bit quantization or if model is already on device
        if not settings.LOAD_IN_8BIT and not hasattr(model, 'hf_device_map'):
            try:
                device = torch.device(settings.DEVICE if torch.cuda.is_available() and settings.DEVICE == "cuda" else "cpu")
                model = model.to(device)
            except RuntimeError as e:
                if "offloaded to cpu or disk" in str(e):
                    logger.info("Model has offloaded modules, skipping device movement")
                else:
                    raise

        return model, processor
        
    except Exception as e:
        logger.exception(f"Failed to load Whisper model: {str(e)}")
        raise



def _ensure_whisper_model(model_name: Optional[str] = None):
    global _model, _processor, _models_cache
    
    # Generate a cache key for the model
    cache_key = f"whisper_{model_name or 'default'}"
    
    # If model is already in cache, use it
    if cache_key in _models_cache:
        _model = _models_cache[cache_key]
        return
        
    # Load the appropriate model based on backend
    if settings.MODEL_BACKEND == "faster_whisper":
        _model = _load_faster_whisper_model(model_name)
        _processor = None
    elif settings.MODEL_BACKEND == "transformers":
        _model, _processor = _load_transformers_whisper_model(model_name)
    
    # Cache the loaded model
    if _model is not None:
        _models_cache[cache_key] = _model

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
    enhance_speech: bool = True,
    should_postprocess: bool = True,
    model_name: Optional[str] = None,
    milliseconds: bool = True,
    **kwargs
) -> dict:
    """
    Run inference with faster-whisper.
    Return dict {"text": ..., "duration": ..., "processing_time": ...}
    Duration is in seconds or milliseconds depending on the flag.
    """
    _ensure_vad_model()
    _ensure_whisper_model(model_name)

    logger.info(
        "Running inference on %s with backend %s and model %s",
        audio_path,
        settings.MODEL_BACKEND,
        model_name or 'default'
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

    do_enhance_speech = False

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
            audio_path = enhanced_path  # Use enhanced file for ASR
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

    text = get_transcript(
        _model, 
        _processor, 
        audio_path, 
        model_backend=settings.MODEL_BACKEND, 
        beam_size=5, 
        language="vi"
    )

    asr_time = time.time() - asr_start
    if milliseconds:
        asr_time = round(asr_time * 1000, 3)
    else:
        asr_time = round(asr_time, 3)

    logger.info("Raw Transcript: %s", text)

    # Postprocess Text
    if should_postprocess:
        text_postprocessing_start = time.time()
        postprocessed_result = postprocess_text(text, _sec_dict, _cpr_model)
        text = postprocessed_result["text"]
        logger.info("Postprocessed Transcript: %s", text)
        text_postprocessing_time = time.time() - text_postprocessing_start
    else:
        text_postprocessing_time = None

    # Calculate processing times
    if text_postprocessing_time is not None and milliseconds:
        text_postprocessing_time = round(text_postprocessing_time * 1000, 3)
    elif text_postprocessing_time is not None:
        text_postprocessing_time = round(text_postprocessing_time, 3)
    
    total_processing_time = time.time() - total_processing_start
    if milliseconds:
        total_processing_time = round(total_processing_time * 1000, 3)
    else:
        total_processing_time = round(total_processing_time, 3)

    # Log the final results
    if milliseconds:
        logger.info(
            "Transcript: %s | Duration: %s ms | ASR Time: %s ms | Text Postprocessing Time: %s | Total Processing Time: %s ms",
            text,
            duration,
            asr_time,
            text_postprocessing_time if text_postprocessing_time is not None else "N/A",
            total_processing_time
        )
    else:
        logger.info(
            "Transcript: %s | Duration: %s s | ASR Time: %s s | Text Postprocessing Time: %s | Total Processing Time: %s s",
            text,
            duration,
            asr_time,
            text_postprocessing_time if text_postprocessing_time is not None else "N/A",
            total_processing_time
        )
    
    # Cleanup temporary enhanced file if it exists
    if do_enhance_speech and 'enhanced_path' in locals() and enhanced_path and os.path.exists(enhanced_path):
        try:
            os.remove(enhanced_path)
            logger.info("Removed temporary enhanced file: %s", enhanced_path)
        except Exception as e:
            logger.warning("Could not remove enhanced file %s: %s", enhanced_path, e)
    
    return {
        "text": text,
        "duration": duration,
        "total_processing_time": total_processing_time,
        "speech_enhancement_time": speech_enhancement_time,
        "asr_time": asr_time,
        "text_postprocessing_time": text_postprocessing_time,
    }
