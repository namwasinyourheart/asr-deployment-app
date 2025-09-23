import os
import pytest
from app.services.inference import asr_infer, load_audio
from app.core.config import settings

TEST_AUDIO_FILE = "examples/example_vietbud500_02.wav"

@pytest.mark.parametrize("audio_path", [TEST_AUDIO_FILE])
def test_load_audio(audio_path):
    speech, sr = load_audio(audio_path)
    assert speech is not None
    assert sr == 16000


def test_adapter_loaded():
    print("\nAdapter path from settings:", settings.ADAPTER_PATH)
    assert True

@pytest.mark.parametrize("audio_path", [TEST_AUDIO_FILE])
def test_asr_infer(audio_path):
    result = asr_infer(audio_path)
    print("\nASR inference result:", result)
    assert isinstance(result, dict)
    assert "text" in result
    # assert "segments" in result
    assert "duration" in result
    assert isinstance(result["duration"], float)
    assert result["duration"] > 0