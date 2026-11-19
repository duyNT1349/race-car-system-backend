import asyncio
import json
import serial
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# 1. List of connected WebSocket clients (browsers)
connected_clients: list[WebSocket] = []

# 2. Connect Serial port to ESP32 
SERIAL_PORT = "COM3"  # Change this to the ESP32's serial port
BAUD_RATE = 115200 # standard baud rate for ESP32

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05)
    print(f"Successfully connected to hardware via {SERIAL_PORT}!")
except Exception as e:
    ser = None
    print(f"Hardware not connected ({e}).")


async def broadcast_to_clients(payload: dict):
    # Package the payload as JSON and send it to all connected WebSocket clients (browsers)
    if not connected_clients:
        return

    message = json.dumps(payload)
    disconnected = []

    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        if client in connected_clients:
            connected_clients.remove(client)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    print("A browser has connected to the Dashboard!")

    try:
        while True:
            #ESP32 -> Backend -> Frontend (Serial data)
            if ser and ser.is_open and ser.in_waiting > 0:
                raw_data = ser.readline().decode("utf-8", errors="ignore").strip()

                if raw_data:
                    print(f"[ESP32 -> Backend] {raw_data}")

                    # Ignore "======"
                    if raw_data.strip("=") == "": continue

                    foul = ("PHAM QUY" in raw_data) or ("XUAT PHAT" in raw_data)

                        # Pakage into JSON to send to frontend
                    frontend_payload = {
                            "text": raw_data, #display text on frontend
                            "status": foul } #sign of foul (True/False) to display on frontend (popup/banner etc.)
                    await broadcast_to_clients(frontend_payload)

            # Frontend -> Backend -> ESP32 (Command data)
            try:
                data_from_web = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                packet = json.loads(data_from_web)
                cmd = packet.get("command", "").strip().lower()

                if ser and ser.is_open:
                    if cmd == "start":
                        ser.write(b"START\n")
                        print("[Backend -> ESP32] Sent START")
                    elif cmd == "reset":
                        ser.write(b"RESET\n")
                        print("[Backend -> ESP32] Sent RESET")

            except asyncio.TimeoutError:
                #loop continues if no data is received from the frontend within the timeout
                pass
            except json.JSONDecodeError:
                print(f"Invalid JSON from web: {data_from_web}")
            #update every 10ms to allow other tasks to run
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print("User disconnected.")


if __name__ == "__main__":
    import uvicorn
#IP address of localhost
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
     