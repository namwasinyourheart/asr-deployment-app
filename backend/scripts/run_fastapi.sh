#!/bin/bash

export WHISPER_HF_MODEL_PATH="/home/nampv1/projects/asr/asr-demo-app/models/merged/vnpost_asr_01_20250920"
export ADAPTER_PATHS=""
# export ADAPTER_PATHS=/home/nampv1/projects/asr/asr-demo-app/models/adapters/on_data1/checkpoint-7434,/home/nampv1/projects/asr/asr-demo-app/models/adapters/on_data2/checkpoint-6500
export DEVICE="cuda"
export LOAD_IN_8BIT=False
export WHISPER_CT2_MODEL_PATH="/home/nampv1/projects/asr/asr-demo-app/models/ct2/vnpost_asr_01_20250920_ct2_fp16"
# export inference_config_path 
export CPR_MODEL_PATH="/home/nampv1/projects/asr/asr-demo-app/models/cpr/capu"
export VAD_MODEL_PATH="/home/nampv1/projects/asr/asr-demo-app/models/vad/snakers4_silero-vad_master"
export SEC_MODEL_PATH="/home/nampv1/projects/asr/asr-demo-app/models/sec/"
export DEEP_FILTER_MODEL_PATH="/home/nampv1/projects/asr/asr-demo-app/models/df/DeepFilterNet2"
export MODEL_BACKEND="transformers"

uvicorn app.main:app --host 0.0.0.0 --port 13081 --reload