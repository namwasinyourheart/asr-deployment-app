# import websocket
# import time

# # Kết nối WebSocket
# ws = websocket.WebSocket()
# ws.connect("ws://localhost:8000/api/v1/asr/chunk")

# # Mở file WAV làm chunk mẫu
# with open("examples/example_vietbud500_01.wav", "rb") as f:
#     chunk_bytes = f.read()

# # Gửi chunk
# ws.send_binary(chunk_bytes)

# # Nhận transcript tạm thời
# msg = ws.recv()
# print("Transcript:", msg)

# # Đóng kết nối
# ws.close()


import websocket
import soundfile as sf
import numpy as np
import io
import time

ws = websocket.WebSocket()
ws.connect("ws://localhost:8000/api/v1/asr/chunk")

# Load WAV
# audio_path = "/home/nampv1/projects/asr/asr-deployment-app/backend/examples/example_vietbud500_03_26s.wav"
audio_path = "/home/nampv1/Downloads/1737530609.3746396.wav"
audio, sr = sf.read(audio_path)

# Chia chunk 2 giây
chunk_size = sr * 3
for i in range(0, len(audio), chunk_size):
    chunk = audio[i:i+chunk_size]
    buf = io.BytesIO()
    sf.write(buf, chunk, sr, format="WAV")
    buf.seek(0)
    ws.send_binary(buf.read())
    msg = ws.recv()
    print("Partial transcript:", msg)
    time.sleep(0.1)

ws.close()
