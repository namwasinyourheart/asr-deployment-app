import os
from typing import Dict, Union, Tuple, Optional
from pydantic import validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model configurations
    MODEL_CONFIGS: Dict[str, Union[str, Tuple[str, str]]] = {
        # Format: "model_name": "path_to_merged_model" or ("base_model", "adapter_path")
        "openai/whisper-large-v3-turbo": "openai/whisper-large-v3-turbo",
        "vnp/stt_a1": "/media/nampv1/hdd/models/asr/models/merged/vnpost_asr_01_20250920",
        "vnp/stt_a2": (
            "openai/whisper-large-v3-turbo",
            "/media/nampv1/hdd/models/asr/models/adapters/train_venterprise_address_hanoi_2__openai_whisper_large_v3_turbo__bs48/venterprise_address_hanoi__openai_whisper_large_v3_turbo__ft_prepared_data_1_lora_r32_a64_bs48_lr1e-5__checkpoints__checkpoint-2200/checkpoint-2200"
        )
    }
    
    # Default model to use if none specified
    DEFAULT_MODEL: str = "vnp/stt_a1"
    
    # Backward compatibility with existing environment variables
    WHISPER_HF_MODEL_PATH: str = os.getenv("WHISPER_HF_MODEL_PATH", "openai/whisper-large-v3-turbo")
    ADAPTER_PATHS: Union[str, list[str], None] = os.getenv("ADAPTER_PATHS", None)  # optional Lora adapter path
    WHISPER_CT2_MODEL_PATH: str = os.getenv("WHISPER_CT2_MODEL_PATH", "")
    VAD_MODEL_PATH: str = os.getenv("VAD_MODEL_PATH", "")
    DEEP_FILTER_MODEL_PATH: str = os.getenv("DEEP_FILTER_MODEL_PATH", "")
    SEC_MODEL_PATH: str = os.getenv("SEC_MODEL_PATH", "")
    CPR_MODEL_PATH: str = os.getenv("CPR_MODEL_PATH", "")
    MODEL_BACKEND: str = os.getenv("MODEL_BACKEND", "faster_whisper")
    DEVICE: str = os.getenv("DEVICE", "cuda")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/asr")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOAD_IN_8BIT: bool = os.getenv("LOAD_IN_8BIT", "False").lower() == "true"
    
    @validator('MODEL_CONFIGS')
    def validate_model_configs(cls, v):
        if not isinstance(v, dict):
            raise ValueError("MODEL_CONFIGS must be a dictionary")
        for model_name, config in v.items():
            if not isinstance(model_name, str):
                raise ValueError(f"Model name must be a string, got {type(model_name)}")
            if not (isinstance(config, str) or 
                   (isinstance(config, tuple) and len(config) == 2 and 
                    all(isinstance(x, str) for x in config))):
                raise ValueError(
                    f"Model config must be a path string or (base_model, adapter_path) tuple, "
                    f"got {type(config)} for model {model_name}"
                )
        return v
    
    def get_model_config(self, model_name: Optional[str] = None) -> Union[str, Tuple[str, str]]:
        """
        Get configuration for the specified model or default model.
        
        Args:
            model_name: Name of the model to get configuration for. If None, uses default model.
            
        Returns:
            Union[str, Tuple[str, str]]: Either a model path string or a tuple of (base_model, adapter_path)
            
        Raises:
            ValueError: If the specified model is not found in configurations
        """
        model_name = model_name or self.DEFAULT_MODEL
        if model_name not in self.MODEL_CONFIGS:
            raise ValueError(f"Model '{model_name}' not found in configurations. "
                           f"Available models: {', '.join(self.MODEL_CONFIGS.keys())}")
        return self.MODEL_CONFIGS[model_name]
    
    def is_adapter_model(self, model_name: Optional[str] = None) -> bool:
        """Check if the specified model uses an adapter."""
        config = self.get_model_config(model_name)
        return isinstance(config, tuple)
    
    def get_base_model(self, model_name: Optional[str] = None) -> str:
        """Get the base model path/name."""
        config = self.get_model_config(model_name)
        return config[0] if isinstance(config, tuple) else config
    
    def get_adapter_path(self, model_name: Optional[str] = None) -> Optional[str]:
        """Get the adapter path if it exists, otherwise return None."""
        config = self.get_model_config(model_name)
        return config[1] if isinstance(config, tuple) else None

settings = Settings()