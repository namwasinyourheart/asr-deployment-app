import io
import requests
import torchaudio

def load_audio(audio_path, target_sr=16000):
    """
    Load audio from file or URL, resample to target_sr.
    Return numpy array and sample rate.
    """
    if audio_path.startswith("http://") or audio_path.startswith("https://"):
        r = requests.get(audio_path, timeout=30)
        r.raise_for_status()
        data = io.BytesIO(r.content)
        waveform, sr = torchaudio.load(data)
    else:
        waveform, sr = torchaudio.load(audio_path)

    # If stereo, select the first channel
    if waveform.shape[0] > 1:
        waveform = waveform[0:1, :]

    # Resample if needed
    if sr != target_sr:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
        waveform = resampler(waveform)

    waveform = waveform.squeeze().numpy()
    return waveform, target_sr


def compute_duration(audio_array, sr: int) -> float:
    """
    Compute audio duration in seconds, rounded to 3 decimal places.
    """
    return round(float(len(audio_array) / sr), 3)


def compute_duration(audio_array, sr: int, milliseconds: bool = False) -> float:
    """
    Compute audio duration, either in seconds or milliseconds, rounded to 3 decimal places.

    Args:
        audio_array: Audio samples (e.g., NumPy array or list)
        sr (int): Sampling rate (samples per second)
        milliseconds (bool): If True, return duration in milliseconds. Defaults to False.

    Returns:
        float: Duration in seconds or milliseconds, rounded to 3 decimal places.
    """
    duration = len(audio_array) / sr
    if milliseconds:
        duration *= 1000
    else:
        duration = round(float(duration), 3)
    return duration
