import torch
from df.enhance import enhance, load_audio, save_audio
from df.enhance import init_df

from app.core.config import settings
from .service_utils import setup_logger

logger = setup_logger(__name__)

_df_model = None
_df_state = None

def _ensure_df_model():
    global _df_model, _df_state
    if _df_model is None or _df_state is None:
        logger.info("Loading DeepFilterNet2 speech enhancement model...")
        _df_model, _df_state, _ = init_df(
            model_base_dir=settings.DEEP_FILTER_MODEL_PATH
        )

_ensure_df_model()


def enhance_speech(
    model,
    df_state,
    input_wav: str,
    output_wav: str,
    device: str = None,
):
    """
    Enhance a noisy speech file using a preloaded DeepFilterNet model.
    Uses DeepFilterNet's own load/save utilities.
    """
    # Auto-detect device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    model.to(device).eval()

    # === Load audio ===
    noisy_audio, meta = load_audio(input_wav)

    # Move to device
    noisy_audio = noisy_audio.to(device)

    # === Enhance ===
    with torch.no_grad():
        # Ensure audio is on CPU before enhancement
        if noisy_audio.is_cuda:
            noisy_audio = noisy_audio.cpu()
        enhanced_audio = enhance(model, df_state, noisy_audio)

    # === Save ===
    # Move to CPU if needed before saving
    if enhanced_audio.is_cuda:
        enhanced_audio = enhanced_audio.cpu()
    target_sr = df_state.sr() if callable(df_state.sr) else df_state.sr
    save_audio(output_wav, enhanced_audio, target_sr)
    print(f"✅ Enhanced audio saved to: {output_wav}")

    return output_wav
