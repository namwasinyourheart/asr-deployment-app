from locust import HttpUser, task, between

class HelloWorldUser(HttpUser):
    host = "http://127.0.0.1:13081"
    wait_time = between(1, 2)

    @task(0)
    def hello(self):
        self.client.get("/")


class ASRUser(HttpUser):
    host = "http://127.0.0.1:13081"
    wait_time = between(2, 4)

    @task(1)
    def upload_audio(self):
        with open("/home/nampv1/projects/asr/asr-demo-app/backend/examples/example_vietbud500_03_26s.wav", "rb") as f:
            files = {
                "audio_file": ("example_vietbud500_03_26s.wav", f, "audio/wav")
            }
            self.client.post("/api/v1/asr/file", files=files)
