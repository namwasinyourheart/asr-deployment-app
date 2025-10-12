import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WHISPER_HF_MODEL_PATH: str = os.getenv("WHISPER_HF_MODEL_PATH", "openai/whisper-large-v3-turbo")
    ADAPTER_PATHS: str | list[str] | None = os.getenv("ADAPTER_PATHS", None) # optional Lora adapter path
    WHISPER_CT2_MODEL_PATH: str = os.getenv("WHISPER_CT2_MODEL_PATH", "")
    VAD_MODEL_PATH: str = os.getenv("VAD_MODEL_PATH", "")
    DEEP_FILTER_MODEL_PATH: str = os.getenv("DEEP_FILTER_MODEL_PATH", "")
    SEC_MODEL_PATH: str = os.getenv("SEC_MODEL_PATH", "")
    CPR_MODEL_PATH: str = os.getenv("CPR_MODEL_PATH", "")
    MODEL_BACKEND: str = os.getenv("MODEL_BACKEND", "faster_whisper")  # whisper
    DEVICE: str = os.getenv("DEVICE", "cuda")  # cpu | cuda
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/asr")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOAD_IN_8BIT: bool = os.getenv("LOAD_IN_8BIT", False)

settings = Settings()