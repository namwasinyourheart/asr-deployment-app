import torch
from df.enhance import enhance, load_audio, save_audio

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
        enhanced_audio = enhance(model, df_state, noisy_audio)

    # === Save ===
    target_sr = df_state.sr() if callable(df_state.sr) else df_state.sr
    save_audio(output_wav, enhanced_audio, target_sr)
    print(f"✅ Enhanced audio saved to: {output_wav}")

    return output_wav
