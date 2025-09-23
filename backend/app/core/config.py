import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HF_MODEL: str = os.getenv("HF_MODEL", "openai/whisper-large-v3-turbo")
    ADAPTER_PATHS: str | list[str] | None = os.getenv("ADAPTER_PATHS", None) # optional Lora adapter path
    MODEL_BACKEND: str = os.getenv("MODEL_BACKEND", "whisper")  # whisper
    DEVICE: str = os.getenv("DEVICE", "cpu")  # cpu | cuda
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/asr")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOAD_IN_8BIT: bool = os.getenv("LOAD_IN_8BIT", False)
    WHISPER_MODEL_CT2: str = os.getenv("WHISPER_MODEL_CT2", "")

settings = Settings()