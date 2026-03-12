import websocket

ws = websocket.WebSocket()
ws.connect("ws://0.0.0.0:13081/asr/v1/ws/transcript")

with open("audio.pcm", "rb") as f:
    while chunk := f.read(3200):   # ~100ms audio
        ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)

ws.send("END")

print(ws.recv())