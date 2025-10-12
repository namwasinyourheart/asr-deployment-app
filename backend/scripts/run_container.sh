# Usage
# Build docker image
# sudo docker build --no-cache -t vnpost-asr-service-1:ct2_fp16 .

# Run docker with nvidia runtime
# sudo docker run --gpus '"device=0"' -it --rm \
# -v /home/nampv1/projects/asr/asr-demo-app/backend:/app \
# -v /home/nampv1/projects/asr/asr-demo-app/models:/app/models \
# -p 13081:13081 vnpost-asr-service-1:ct2_fp16


# sudo docker run --env DEVICE=cpu -it --rm \
# -v /home/nampv1/projects/asr/asr-demo-app/backend:/app \
# -v /home/nampv1/projects/asr/asr-demo-app/models:/app/models \
# -p 13081:13081 vnpost-asr-service-1:ct2_fp16
