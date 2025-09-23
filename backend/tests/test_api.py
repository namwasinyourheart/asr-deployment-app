import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)



def test_asr_with_file():
    with open("examples/example_vietbud500_01.wav", "rb") as f:
        response = client.post(
            "/api/v1/asr/file",
            files={"audio_file": ("example.wav", f, "audio/wav")}
        )
    assert response.status_code == 200
    data = response.json()
    print("\nASR inference response:", data)
    assert "text" in data
    # assert "segments" in data
    assert "duration" in data
    assert isinstance(data["duration"], float)
    assert data["duration"] > 0

def test_asr_with_url():
    url = "https://drive.google.com/uc?export=download&id=1CcyHCXoS5m9ILgBsWY-RZY52JNaZjjge"
    response = client.post("/api/v1/asr/url", data={"audio_url": url})
    
    assert response.status_code == 200
    data = response.json()
    print("\nASR inference response:", data)
    assert "text" in data
    # assert "segments" in data
    assert "duration" in data
    assert isinstance(data["duration"], float)
    assert data["duration"] > 0
