import csv
import time
from locust import HttpUser, task, between, events, constant

# Mở file CSV để log
csv_file = open("/home/nampv1/projects/asr/asr-demo-app/tests/test_load/asr_test_log.csv", mode="w", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "user_id", "request_id", "endpoint", "status_code", "response_time_ms", "response_text"])

# Biến đếm request toàn cục
global_request_id = 0

class ASRUser(HttpUser):
    host = "http://127.0.0.1:13081"
    # wait_time = between(1, 2)
    wait_time = constant(1)

    @task
    def asr_request(self):
        global global_request_id
        global_request_id += 1

        request_id = global_request_id
        user_id = id(self)  # hoặc bạn có thể tự generate user_id từ 1..10

        # Ghi lại thời điểm gửi request
        start_time = time.time()
        with open("/home/nampv1/projects/asr/asr-demo-app/backend/examples/example_vietbud500_03_26s.wav", "rb") as f:
            files = {"audio_file": ("1738232476.3986811.wav", f, "audio/wav")}
            response = self.client.post("/api/v1/asr/file", files=files, name="ASR Upload")
        
        # Tính thời gian phản hồi
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)

        # Lấy timestamp dạng ISO
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))

        # Ghi log vào CSV
        csv_writer.writerow([
            timestamp,
            user_id,
            request_id,
            "/api/v1/asr/file",
            response.status_code,
            elapsed_ms,
            response.text.strip()[:200]  # cắt ngắn response nếu quá dài
        ])
        csv_file.flush()  # đảm bảo dữ liệu được ghi ngay
