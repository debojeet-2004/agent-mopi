# from faster_whisper import WhisperModel

# model_size = "small"

# model = WhisperModel(
#     model_size,
#     device="cuda",
#     compute_type="float16"
# )

# segments, _ = model.transcribe(
#     "audio.mp3",
#     language="en",
#     beam_size=5
# )

# for segment in segments:
#     print(segment.text)
    
    
    
import sounddevice as sd
import numpy as np
import queue
import threading

from faster_whisper import WhisperModel


# -----------------------------------
# Settings
# -----------------------------------

samplerate = 16000
block_duration = 2       # seconds
chunk_duration = 5         # seconds
channels = 1

frames_per_block = int(
    samplerate * block_duration
)

frames_per_chunk = int(
    samplerate * chunk_duration
)


audio_queue = queue.Queue()
audio_buffer = []


# -----------------------------------
# Model setup
# -----------------------------------

model = WhisperModel(
    "small",  # "tiny", "base", "small", "medium", "large-v1", "large-v2"
    device="cpu",
    compute_type="int8"
)


# -----------------------------------
# Audio callback
# -----------------------------------

def audio_callback(indata, frames, time, status):

    if status:
        print(status)

    audio_queue.put(indata.copy())


# -----------------------------------
# Recorder
# -----------------------------------

def recorder():

    with sd.InputStream(
        samplerate=samplerate,
        channels=channels,
        callback=audio_callback,
        blocksize=frames_per_block
    ):

        print("🎙️ Listening... Press Ctrl+C to stop.")

        while True:
            sd.sleep(100)


# -----------------------------------
# Transcriber
# -----------------------------------

def transcriber():

    global audio_buffer

    while True:

        block = audio_queue.get()

        audio_buffer.append(block)

        total_frames = sum(
            len(b) for b in audio_buffer
        )

        if total_frames >= frames_per_chunk:

            audio_data = np.concatenate(
                audio_buffer
            )[:frames_per_chunk]

            audio_buffer = []

            audio_data = (
                audio_data
                .flatten()
                .astype(np.float32)
            )


            # -----------------------------------
            # Transcription
            # -----------------------------------

            segments, _ = model.transcribe(
                audio_data,
                language="en",
                beam_size=5
            )


            for segment in segments:

                print(
                    f"{segment.text}"
                )


# -----------------------------------
# Start threads
# -----------------------------------

threading.Thread(
    target=recorder,
    daemon=True
).start()

transcriber()