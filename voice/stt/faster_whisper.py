import os

VENV = os.environ["VIRTUAL_ENV"]

CUDA_DIRS = [
    os.path.join(VENV, "Lib", "site-packages", "nvidia", "cublas", "bin"),
    os.path.join(VENV, "Lib", "site-packages", "nvidia", "cudnn", "bin"),
    os.path.join(VENV, "Lib", "site-packages", "nvidia", "cuda_nvrtc", "bin"),
]

for directory in CUDA_DIRS:
    os.add_dll_directory(directory)

os.environ["PATH"] = os.pathsep.join(CUDA_DIRS) + os.pathsep + os.environ["PATH"]

from faster_whisper import WhisperModel

MODEL_SIZE = "small.en"  # "tiny", "base", "small", "medium", "large-v1", "large-v2"

model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")


def transcribe(audio_array, sample_rate: int = 16000) -> str:
    """
    audio_array: 1D numpy float32 array (the concatenated speech buffer)
    Returns the transcribed text as a plain string.
    """
    segments, info = model.transcribe(audio_array, beam_size=5, language="en")

    text = "".join(segment.text for segment in segments)
    # print (info)
    return text.strip()
    # return {"info": info, "content": text.strip()}
