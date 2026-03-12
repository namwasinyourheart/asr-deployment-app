from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import numpy as np
import uuid
import logging
import json

from app.services.inference import asr_infer

router = APIRouter()
logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
WINDOW_SECONDS = 3
WINDOW_SIZE = SAMPLE_RATE * WINDOW_SECONDS

@router.websocket("/ws/transcript")
async def websocket_transcribe(websocket: WebSocket):

    await websocket.accept()

    session_id = str(uuid.uuid4())
    logger.info(f"Session start {session_id}")

    audio_buffer = np.array([], dtype=np.float32)
    turn_order = 0

    try:

        # session start message
        await websocket.send_json({
            "type": "SessionBegins"
        })

        while True:

            message = await websocket.receive()

            # AUDIO BINARY
            if "bytes" in message:

                chunk = message["bytes"]

                audio = np.frombuffer(
                    chunk,
                    dtype=np.int16
                ).astype(np.float32) / 32768.0

                audio_buffer = np.concatenate([audio_buffer, audio])

                if len(audio_buffer) >= WINDOW_SIZE:

                    # run ASR directly on numpy
                    result = asr_infer(
                        audio_buffer,
                        sample_rate=SAMPLE_RATE,
                        do_enhance_speech=True,
                        do_postprocess_text=True,
                        model_name="vnp/stt_a1",
                        milliseconds=True,
                    )

                    await websocket.send_json({
                        "type": "Turn",
                        "turn_order": turn_order,
                        "transcript": result["text"]
                    })

                    turn_order += 1

                    # sliding window (giữ lại 0.5s context)
                    audio_buffer = audio_buffer[int(SAMPLE_RATE * 0.5):]

            # COMMAND
            elif "text" in message:

                data = json.loads(message["text"])

                if data.get("type") == "Terminate":

                    if len(audio_buffer) > 0:

                        result = asr_infer(
                            audio_buffer,
                            sample_rate=SAMPLE_RATE,
                            do_enhance_speech=True,
                            do_postprocess_text=True,
                            model_name="vnp/stt_a1",
                            milliseconds=True,
                        )

                        await websocket.send_json({
                            "type": "Turn",
                            "turn_order": turn_order,
                            "transcript": result["text"]
                        })

                    await websocket.send_json({
                        "type": "SessionTerminated"
                    })

                    break

    except WebSocketDisconnect:

        logger.info(f"Session disconnected {session_id}")



# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# import numpy as np
# import uuid
# import logging
# import json
# import tempfile
# import os
# import soundfile as sf

# from app.services.inference import asr_infer

# router = APIRouter()
# logger = logging.getLogger(__name__)

# SAMPLE_RATE = 16000
# WINDOW_SECONDS = 2
# WINDOW_SIZE = SAMPLE_RATE * WINDOW_SECONDS


# @router.websocket("/ws/transcript")
# async def websocket_transcribe(websocket: WebSocket):

#     await websocket.accept()

#     session_id = str(uuid.uuid4())
#     logger.info(f"Session start {session_id}")

#     # send session start event
#     await websocket.send_json({
#         "type": "SessionBegins"
#     })

#     audio_buffer = np.array([], dtype=np.float32)
#     final_audio = []

#     turn_order = 0

#     try:

#         while True:

#             message = await websocket.receive()

#             # AUDIO BYTES
#             if "bytes" in message:

#                 chunk = message["bytes"]

#                 # convert PCM16 -> float32
#                 audio = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

#                 audio_buffer = np.concatenate([audio_buffer, audio])
#                 final_audio.append(audio)

#                 if len(audio_buffer) >= WINDOW_SIZE:

#                     logger.info("Processing audio window")

#                     # ghi wav tạm cho model
#                     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#                         tmp_path = tmp.name

#                     sf.write(tmp_path, audio_buffer, SAMPLE_RATE)

#                     try:

#                         result = asr_infer(
#                             tmp_path,
#                             do_enhance_speech=True,
#                             do_postprocess_text=True,
#                             model_name="vnp/stt_a1",
#                             milliseconds=True,
#                         )

#                         await websocket.send_json({
#                             "type": "Turn",
#                             "turn_order": turn_order,
#                             "transcript": result["text"]
#                         })

#                         turn_order += 1

#                     finally:
#                         os.remove(tmp_path)

#                     # reset window
#                     audio_buffer = np.array([], dtype=np.float32)

#             # TEXT MESSAGE (Terminate command)
#             elif "text" in message:

#                 try:
#                     data = json.loads(message["text"])
#                 except:
#                     continue

#                 if data.get("type") == "Terminate":

#                     logger.info("Terminate received")

#                     if len(final_audio) == 0:
#                         break

#                     full_audio = np.concatenate(final_audio)

#                     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#                         tmp_path = tmp.name

#                     sf.write(tmp_path, full_audio, SAMPLE_RATE)

#                     try:

#                         result = asr_infer(
#                             tmp_path,
#                             do_enhance_speech=True,
#                             do_postprocess_text=True,
#                             model_name="vnp/stt_a1",
#                             milliseconds=True,
#                         )

#                         await websocket.send_json({
#                             "type": "Turn",
#                             "turn_order": turn_order,
#                             "transcript": result["text"]
#                         })

#                     finally:
#                         os.remove(tmp_path)

#                     await websocket.send_json({
#                         "type": "SessionTerminated"
#                     })

#                     break

#     except WebSocketDisconnect:
#         logger.info(f"Session disconnected {session_id}")


# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# import numpy as np
# import tempfile
# import os
# import uuid
# import logging
# import soundfile as sf
# from app.services.inference import asr_infer

# router = APIRouter()
# logger = logging.getLogger(__name__)

# SAMPLE_RATE = 16000
# WINDOW_SECONDS = 2
# WINDOW_SIZE = SAMPLE_RATE * WINDOW_SECONDS

# @router.websocket("/ws/transcript")
# async def websocket_transcribe(websocket: WebSocket):

#     await websocket.accept()
#     session_id = str(uuid.uuid4())

#     logger.info(f"Session start {session_id}")

#     audio_buffer = np.array([], dtype=np.float32)
#     final_audio = []

#     try:
#         while True:

#             message = await websocket.receive()

#             # binary audio chunk
#             if "bytes" in message:

#                 chunk = message["bytes"]

#                 audio = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

#                 audio_buffer = np.concatenate([audio_buffer, audio])
#                 final_audio.append(audio)

#                 print("Length audio buffer: ", len(audio_buffer))

#                 if len(audio_buffer) >= WINDOW_SIZE:
#                     print("Processing audio buffer...")

#                     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#                         tmp_path = tmp.name

#                     sf.write(tmp_path, audio_buffer, SAMPLE_RATE)

#                     try:
#                         result = asr_infer(
#                             tmp_path,
#                             do_enhance_speech=True,
#                             do_postprocess_text=True,
#                             model_name="vnp/stt_a1",
#                             milliseconds=True,
#                         )

#                         await websocket.send_json({
#                             "type": "partial",
#                             "text": result["text"]
#                         })

#                     finally:
#                         os.remove(tmp_path)

#                     audio_buffer = np.array([], dtype=np.float32)

#             # command
#             elif "text" in message:

#                 if message["text"] == "END":

#                     full_audio = np.concatenate(final_audio)

#                     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#                         tmp_path = tmp.name

#                     sf.write(tmp_path, full_audio, SAMPLE_RATE)

#                     result = asr_infer(
#                         tmp_path,
#                         do_enhance_speech=True,
#                         do_postprocess_text=True,
#                         model_name="vnp/stt_a1",
#                         milliseconds=True,
#                     )

#                     await websocket.send_json({
#                         "type": "final",
#                         "text": result["text"]
#                     })

#                     os.remove(tmp_path)
#                     break

#     except WebSocketDisconnect:
#         logger.info(f"Session disconnected {session_id}")