import queue

from voice.stt.faster_whisper import transcribe
from voice.vad.silero_vad import SAMPLE_RATE


# -----------------------------------
# QUEUES
# -----------------------------------

# Audio waiting to be transcribed
stt_queue = queue.Queue()

# Completed transcriptions
transcript_queue = queue.Queue()


# -----------------------------------
# STT WORKER
# -----------------------------------

def stt_worker():
    """
    Continuously takes audio from stt_queue,
    transcribes it using Faster-Whisper,
    and puts the resulting text into transcript_queue.
    """

    while True:

        audio = stt_queue.get()

        try:

            text = transcribe(
                audio,
                sample_rate=SAMPLE_RATE
            )

            if text:
                transcript_queue.put(text)

        finally:

            stt_queue.task_done()