#!/bin/bash
# export HF_MODEL="openai/whisper-tiny"
# export HF_MODEL="openai/whisper-base"
# export HF_MODEL="openai/whisper-large-v3"
export HF_MODEL="/home/nampv1/projects/asr/asr-demo-app/models/merged/vnpost_asr_01_20250920"
export ADAPTER_PATHS=""
# export ADAPTER_PATHS=/home/nampv1/projects/asr/asr-demo-app/models/adapters/on_data1/checkpoint-7434,/home/nampv1/projects/asr/asr-demo-app/models/adapters/on_data2/checkpoint-6500
export DEVICE="cuda"
export LOAD_IN_8BIT=False
export WHISPER_MODEL_CT2="/home/nampv1/projects/asr/asr-demo-app/models/ct2/vnpost_asr_01_20250920_ct2_fp16"
# export inference_config_path 

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload