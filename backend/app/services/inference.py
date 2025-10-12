import logging
import torch
import soundfile as sf
import librosa
import requests
import io
from app.core.config import settings

logger = logging.getLogger(__name__)

_model = None
_processor = None
_backend = None

# def load_audio(audio_path, target_sr=16000):
#     # Nếu là URL thì tải về trước
#     if audio_path.startswith("http://") or audio_path.startswith("https://"):
#         response = requests.get(audio_path)
#         response.raise_for_status()
#         data = io.BytesIO(response.content)
#         audio_array, sr = sf.read(data)
#     else:
#         audio_array, sr = sf.read(audio_path)

#     # Resample nếu cần
#     if sr != target_sr:
#         audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=target_sr)
#         sr = target_sr

#     # Nếu stereo, lấy kênh đầu tiên
#     if len(audio_array.shape) > 1:
#         audio_array = audio_array[:, 0]

#     print("audio_array shape: ", audio_array.shape)
#     print("sampling rate: ", sr)

#     return audio_array, sr


import torchaudio

def load_audio(audio_path, target_sr=16000):
    # Nếu là URL thì tải về trước
    if audio_path.startswith("http://") or audio_path.startswith("https://"):
        with httpx.Client(timeout=30) as client:
            r = client.get(audio_path)
            r.raise_for_status()
            data = io.BytesIO(r.content)
        waveform, sr = torchaudio.load(data)
    else:
        waveform, sr = torchaudio.load(audio_path)  # waveform shape: [channels, samples]

    # Nếu stereo, lấy kênh đầu tiên
    if waveform.shape[0] > 1:
        waveform = waveform[0:1, :]

    # Resample nếu cần
    if sr != target_sr:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
        waveform = resampler(waveform)

    waveform = waveform.squeeze().numpy()
    # print("audio_array shape:", waveform.shape)
    # print("sampling rate:", target_sr)
    return waveform, target_sr


def compute_duration(audio_array, sr: int) -> float:
    """
    Compute audio duration in seconds, round to 3 decimal places
    """
    return round(float(len(audio_array) / sr), 3)


def _load_whisper_model():
    try:
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
        from peft import PeftModel

        model_name = settings.WHISPER_MODEL  # ví dụ: "openai/whisper-small"
        logger.info("Loading Whisper model: %s", model_name)

        processor = WhisperProcessor.from_pretrained(model_name)
        # processor.feature_extractor.chunk_length=120
        # print("processor.feature_extractor.chunk_length:", processor.feature_extractor.chunk_length)
        model = WhisperForConditionalGeneration.from_pretrained(model_name, load_in_8bit=settings.LOAD_IN_8BIT)

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
        print("settings.LOAD_IN_8BIT:", settings.LOAD_IN_8BIT)
        if not settings.LOAD_IN_8BIT:
            if settings.DEVICE == "cuda" and torch.cuda.is_available():
                model = model.to("cuda")
            else:
                model = model.to("cpu")

        return model, processor
    except Exception as e:
        logger.exception("Failed to load Whisper model: %s", e)
        raise


def _ensure_model():
    global _model, _processor, _backend
    if _model is not None and _processor is not None:
        return
    _model, _processor = _load_whisper_model()
    _backend = "whisper"

import time

def asr_infer(audio_path: str) -> dict:
    """
    Run inference using HuggingFace Whisper model directly.
    Returns dict {"text": ..., "duration": ..., "processing_time": ...}
    """
    _ensure_model()

    if _backend == "whisper":
        logger.info("Running Whisper inference on %s", audio_path)

        processing_start = time.time()

        # Load audio
        # start_time_for_load_audio = time.time()
        audio_array, sr = load_audio(audio_path)
        # end_time_for_load_audio = time.time()
        # load_audio_time = round(end_time_for_load_audio - start_time_for_load_audio, 3)
        # print("Load audio time: %s seconds" % load_audio_time)

        inputs = _processor(audio_array, sampling_rate=sr, return_tensors="pt")
        input_features = inputs.input_features

        # device = "cuda" if settings.DEVICE == "cuda" and torch.cuda.is_available() else "cpu"
        input_features = input_features.to(_model.device, dtype=_model.dtype)

        with torch.no_grad():
            # predicted_ids = _model.generate(input_features)
            predicted_ids = _model.generate(input_features, return_timestamps=True)

        transcription = _processor.batch_decode(predicted_ids, skip_special_tokens=True)
        text = transcription[0] if transcription else ""

        # start_time_for_compute_duration = time.time()
        duration = compute_duration(audio_array, sr)
        # end_time_for_compute_duration = time.time()
        # compute_duration_time = round(end_time_for_compute_duration - start_time_for_compute_duration, 3)
        # print("Compute duration time: %s seconds" % compute_duration_time)
        processing_time = round(time.time() - processing_start, 3)

        logger.info("Transcription: %s", text)
        logger.info("Duration: %s seconds", duration)
        logger.info("Time for ASR: %s seconds", processing_time)

        return {
            "text": text,
            "duration": duration,
            "processing_time": processing_time,
        }
    else:
        return {
            "text": "",
            "duration": None,
            "processing_time": None,
        }
