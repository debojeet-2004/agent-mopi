import sounddevice as sd
import numpy as np
import threading
import torch
import warnings
import queue
import time


# -----------------------------------
# WARNINGS
# -----------------------------------

warnings.filterwarnings(
    "ignore",
    message="`torch.jit.load` is deprecated"
)


# -----------------------------------
# IMPORTS
# -----------------------------------

from voice.vad.silero_vad import (
    is_speech,
    SAMPLE_RATE,
    CHUNK_SIZE
)

from voice.stt.stt_worker import (
    stt_queue,
    transcript_queue,
    stt_worker
)


# -----------------------------------
# CONFIG
# -----------------------------------

SHORT_SILENCE_SECONDS = 0.65
LONG_SILENCE_SECONDS = 4.5

CHUNK_DURATION = CHUNK_SIZE / SAMPLE_RATE

SHORT_SILENCE_CHUNKS = int(
    SHORT_SILENCE_SECONDS / CHUNK_DURATION
)

LONG_SILENCE_CHUNKS = int(
    LONG_SILENCE_SECONDS / CHUNK_DURATION
)

TYPE_DELAY = 0.030


# -----------------------------------
# STATE
# -----------------------------------

speech_buffer = []

is_recording = False

silence_chunk_count = 0

listening = True

finish_event = threading.Event()

completed_transcripts = []


# -----------------------------------
# QUEUES
# -----------------------------------

# Transcript → terminal display
display_queue = queue.Queue()

# Final transcript → run()
final_text_queue = queue.Queue()


# -----------------------------------
# WORKER STATE
# -----------------------------------

_stt_thread = None
_display_thread = None


# -----------------------------------
# TERMINAL TYPING EFFECT
# -----------------------------------

def type_text(text):

    for char in text:

        print(
            char,
            end="",
            flush=True
        )

        time.sleep(TYPE_DELAY)

    print()


# -----------------------------------
# DISPLAY WORKER
# -----------------------------------

def display_worker():

    while True:

        text = display_queue.get()

        try:

            if text is None:
                break

            type_text(text)

        finally:

            display_queue.task_done()


# -----------------------------------
# START STT WORKER
# -----------------------------------

def start_stt_worker():

    global _stt_thread

    if (
        _stt_thread is None
        or not _stt_thread.is_alive()
    ):

        _stt_thread = threading.Thread(
            target=stt_worker,
            daemon=True
        )

        _stt_thread.start()


# -----------------------------------
# START DISPLAY WORKER
# -----------------------------------

def start_display_worker():

    global _display_thread

    if (
        _display_thread is None
        or not _display_thread.is_alive()
    ):

        _display_thread = threading.Thread(
            target=display_worker,
            daemon=True
        )

        _display_thread.start()


# -----------------------------------
# AUDIO CALLBACK
# -----------------------------------

def audio_callback(
    indata,
    frames,
    time_info,
    status
):

    global speech_buffer
    global is_recording
    global silence_chunk_count
    global listening

    # Ignore microphone input
    # when listening has stopped.
    if not listening:
        return

    audio_chunk = indata[:, 0].copy()

    chunk_tensor = torch.from_numpy(
        audio_chunk
    )

    speech_detected = is_speech(
        chunk_tensor
    )


    # --------------------------------
    # SPEECH DETECTED
    # --------------------------------

    if speech_detected:

        speech_buffer.append(
            audio_chunk
        )

        is_recording = True

        silence_chunk_count = 0

        return


    # --------------------------------
    # SILENCE
    # --------------------------------

    if not is_recording:
        return

    silence_chunk_count += 1


    # --------------------------------
    # SHORT SILENCE
    # --------------------------------

    if (
        silence_chunk_count
        == SHORT_SILENCE_CHUNKS
    ):

        send_audio_to_stt()


    # --------------------------------
    # LONG SILENCE
    # --------------------------------

    if (
        silence_chunk_count
        >= LONG_SILENCE_CHUNKS
    ):

        finish_event.set()


# -----------------------------------
# SEND AUDIO TO STT
# -----------------------------------

def send_audio_to_stt():

    global speech_buffer

    if not speech_buffer:
        return

    full_audio = np.concatenate(
        speech_buffer
    )

    # Immediately clear the buffer
    # so new speech can be captured.
    speech_buffer = []

    # Send audio to background STT.
    stt_queue.put(full_audio)


# -----------------------------------
# PROCESS STT RESULTS
# -----------------------------------

def process_completed_transcripts():

    global completed_transcripts

    while True:

        try:

            text = transcript_queue.get_nowait()

        except queue.Empty:

            break


        try:

            if text:

                # Store transcript
                # for final LLM input.
                completed_transcripts.append(
                    text
                )

                # Send transcript
                # to terminal display.
                display_queue.put(
                    f"[You] {text}"
                )

        finally:

            transcript_queue.task_done()


# -----------------------------------
# FINISH LISTENING
# -----------------------------------

def finish_listening():

    global listening
    global speech_buffer
    global is_recording
    global silence_chunk_count

    # --------------------------------
    # STOP MICROPHONE
    # --------------------------------

    listening = False


    # --------------------------------
    # SEND REMAINING AUDIO
    # --------------------------------

    if speech_buffer:

        send_audio_to_stt()


    # --------------------------------
    # WAIT FOR STT
    # --------------------------------

    stt_queue.join()


    # --------------------------------
    # COLLECT FINAL STT RESULTS
    # --------------------------------

    process_completed_transcripts()


    # --------------------------------
    # WAIT FOR TERMINAL DISPLAY
    # --------------------------------

    display_queue.join()


    # --------------------------------
    # BUILD FINAL TEXT
    # --------------------------------

    final_text = (
        " ".join(
            completed_transcripts
        )
        .strip()
    )


    # --------------------------------
    # RESET TEMPORARY STATE
    # --------------------------------

    speech_buffer = []

    is_recording = False

    silence_chunk_count = 0


    return final_text


# -----------------------------------
# CONTROLLER
# -----------------------------------

def controller():

    global listening

    while listening:

        # Wake up every 100ms
        # to check for STT results.
        finish_event.wait(
            timeout=0.1
        )


        # Display completed
        # transcription results.
        process_completed_transcripts()


        # --------------------------------
        # LONG SILENCE DETECTED
        # --------------------------------

        if finish_event.is_set():

            final_text = finish_listening()

            final_text_queue.put(
                final_text
            )

            break


# -----------------------------------
# RUN VOICE SESSION
# -----------------------------------

def run(menu_event=None):

    global listening
    global speech_buffer
    global is_recording
    global silence_chunk_count
    global completed_transcripts


    # --------------------------------
    # RESET SESSION
    # --------------------------------

    listening = True

    speech_buffer = []

    is_recording = False

    silence_chunk_count = 0

    completed_transcripts = []

    finish_event.clear()


    # --------------------------------
    # START STT WORKER
    # --------------------------------

    start_stt_worker()


    # --------------------------------
    # START DISPLAY WORKER
    # --------------------------------

    start_display_worker()


    # --------------------------------
    # START CONTROLLER
    # --------------------------------

    controller_thread = threading.Thread(
        target=controller,
        daemon=True
    )

    controller_thread.start()


    print(
        "\n[Listening...]\n",
        flush=True
    )


    # --------------------------------
    # START MICROPHONE
    # --------------------------------

    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=CHUNK_SIZE,
            callback=audio_callback,
        ):

            while listening:

                # ----------------------------
                # CTRL + M
                # ----------------------------

                if (
                    menu_event is not None
                    and menu_event.is_set()
                ):

                    listening = False

                    break


                sd.sleep(100)


    except KeyboardInterrupt:

        listening = False

        raise


    # --------------------------------
    # CTRL + M → MAIN MENU
    # --------------------------------

    if (
        menu_event is not None
        and menu_event.is_set()
    ):

        # Discard current unfinished speech.
        speech_buffer = []

        is_recording = False

        silence_chunk_count = 0

        # Allow controller thread to exit.
        listening = False

        controller_thread.join(
            timeout=1.0
        )

        return "__BACK_TO_MENU__"


    # --------------------------------
    # WAIT FOR CONTROLLER
    # --------------------------------

    controller_thread.join()


    # --------------------------------
    # GET FINAL TRANSCRIPT
    # --------------------------------

    final_text = final_text_queue.get()


    # --------------------------------
    # NORMALIZE TRANSCRIPT
    # --------------------------------

    final_text = " ".join(
        final_text.split()
    )


    return final_text


# -----------------------------------
# DIRECT EXECUTION
# -----------------------------------

if __name__ == "__main__":

    run()