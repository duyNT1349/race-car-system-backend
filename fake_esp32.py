import asyncio
import websockets
import json

async def simulate_esp32():
    uri = "ws://localhost:8000/ws"
    print("[Fake ESP32] Đang kết nối tới Backend FastAPI...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[Fake ESP32] Đã kết nối thành công! Bắt đầu giả lập gửi dữ liệu...")
            counter = 0
            
            while True:
                counter += 1
                
                # Tạo dữ liệu giả lập (đếm ngược, trạng thái phạm quy, thời gian chạy của xe)
                fake_data = {
                    "countdown": 3 if counter % 15 < 3 else 0,
                    "status_foul": True if counter == 10 else False,
                    "lap_time_car1": f"01:{counter:02d}.50"
                }
                
                # Chuyển dictionary thành chuỗi JSON string để gửi đi
                message = json.dumps(fake_data)
                
                # Gửi dữ liệu lên Backend
                await websocket.send(message)
                print(f"[Fake ESP32] Đã gửi: {message}")
                
                # Chờ 2 giây rồi gửi gói tiếp theo
                await asyncio.sleep(2)
                
    except Exception as e:
        print(f"[!] Mất kết nối tới backend: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_esp32())