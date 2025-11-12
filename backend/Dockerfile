FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04


RUN apt-get update && apt-get install -y --no-install-recommends \
python3.11 python3-pip ffmpeg libsndfile1 git \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

ENV WHISPER_MODEL_PATH="/app/models/merged/vnpost_asr_01_20250920"
ENV WHISPER_CT2_MODEL_PATH="/app/models/ct2/vnpost_asr_01_20250920_ct2_fp16"
ENV ADAPTER_PATHS=""
ENV DEVICE="cuda"
ENV LOAD_IN_8BIT=False
ENV VAD_MODEL_PATH="/app/models/vad/snakers4_silero-vad_master"
ENV DEEP_FILTER_MODEL_PATH="/app/models/df/DeepFilterNet2"
ENV SEC_MODEL_PATH="/app/models/sec/"
ENV CPR_MODEL_PATH="/app/models/cpr/capu"

# ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH

EXPOSE 13081

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "13081"]


# Usage
# Build docker image
# sudo docker build --no-cache -t vnpost-asr-service-1:ct2_fp16 .

# Run docker with nvidia runtime
# sudo docker run -d --gpus '"device=0"' -it --rm \
# -v /home/nampv1/projects/asr/asr-demo-app/backend:/app \
# -v /media/nampv1/hdd/models/asr/models:/app/models \
# -p 13081:13081 vnpost-asr-service-1:ct2_fp16


# sudo docker run --env DEVICE=cpu -it --rm \
# -v /home/nampv1/projects/asr/asr-demo-app/backend:/app \
# -v /media/nampv1/hdd/models/asr/models:/app/models \
# -p 13081:13081 vnpost-asr-service-1:ct2_fp16

