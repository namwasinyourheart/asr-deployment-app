import logging
import time
import io
import requests
import torchaudio

from app.core.config import settings
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

_model = None
_backend = None


def load_audio(audio_path, target_sr=16000):
    """
    Load audio từ file hoặc URL, resample về target_sr.
    Trả về numpy array và sample rate.
    """
    if audio_path.startswith("http://") or audio_path.startswith("https://"):
        r = requests.get(audio_path, timeout=30)
        r.raise_for_status()
        data = io.BytesIO(r.content)
        waveform, sr = torchaudio.load(data)
    else:
        waveform, sr = torchaudio.load(audio_path)

    # Nếu stereo, lấy kênh đầu tiên
    if waveform.shape[0] > 1:
        waveform = waveform[0:1, :]

    # Resample nếu cần
    if sr != target_sr:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
        waveform = resampler(waveform)

    waveform = waveform.squeeze().numpy()
    return waveform, target_sr


def compute_duration(audio_array, sr: int) -> float:
    """
    Tính độ dài audio (giây), làm tròn 3 chữ số thập phân.
    """
    return round(float(len(audio_array) / sr), 3)


def _load_faster_whisper_model():
    """
    Load mô hình faster-whisper từ config.
    """
    try:
        model_path = settings.WHISPER_MODEL_CT2  # ví dụ: đường dẫn tới model đã convert ct2
        logger.info("Loading faster-whisper model: %s", model_path)

        # Bạn có thể config DEVICE (cpu/cuda) và compute_type (float16/int8)
        model = WhisperModel(
            model_path,
            device=settings.DEVICE,
            compute_type="float16" if settings.DEVICE == "cuda" else "int8",
        )
        return model
    except Exception as e:
        logger.exception("Failed to load faster-whisper model: %s", e)
        raise


def _ensure_model():
    global _model, _backend
    if _model is not None:
        return
    _model = _load_faster_whisper_model()
    _backend = "faster-whisper"


def asr_infer(audio_path: str) -> dict:
    """
    Chạy inference với faster-whisper.
    Trả về dict {"text": ..., "duration": ..., "processing_time": ...}
    """
    _ensure_model()

    if _backend == "faster-whisper":
        logger.info("Running faster-whisper inference on %s", audio_path)

        processing_start = time.time()

        # Load audio chỉ để tính duration, vì faster-whisper có thể nhận path trực tiếp
        audio_array, sr = load_audio(audio_path)
        duration = compute_duration(audio_array, sr)

        # Transcribe
        segments, info = _model.transcribe(audio_path, beam_size=5)

        text = " ".join([seg.text for seg in segments])
        processing_time = round(time.time() - processing_start, 3)

        logger.info("Transcription: %s", text)
        logger.info("Duration: %s seconds", duration)
        logger.info("Processing time: %s seconds", processing_time)

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
