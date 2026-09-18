# Audio → speech / silence

# SileroVAD
#     ↓
# is_speech(audio)


import torch
from silero_vad import load_silero_vad

# Load once, reuse everywhere
model = load_silero_vad()

SAMPLE_RATE = 16000  # Silero requires 16000 or 8000 Hz
CHUNK_SIZE = 512  # required chunk size for 16kHz (per Silero docs)


def is_speech(chunk: torch.Tensor, threshold: float = 0.5) -> bool:
    """
    chunk: a 1D float32 torch tensor of exactly CHUNK_SIZE samples
    Returns True if this chunk is classified as speech.
    """
    with torch.no_grad():
        speech_prob = model(chunk, SAMPLE_RATE).item()
    return speech_prob >= threshold
