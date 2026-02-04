#!/bin/bash
export MODELS_DIR="/media/nampv1/hdd/models/asr"
# export WHISPER_HF_MODEL_PATH="/media/nampv1/hdd/models/asr/models/merged/vnpost_asr_01_20250920"
export WHISPER_HF_MODEL_PATH="openai/whisper-large-v3-turbo"
# export ADAPTER_PATHS=/home/nampv1/projects/asr/asr-demo-app/models/adapters/on_data1/checkpoint-7434,/home/nampv1/projects/asr/asr-demo-app/models/adapters/on_data2/checkpoint-6500
export ADAPTER_PATHS="/media/nampv1/hdd/models/asr/adapters/vnp__stt_a2/checkpoint-2200"
export DEVICE="cuda"
export LOAD_IN_8BIT=False
export WHISPER_CT2_MODEL_PATH="/media/nampv1/hdd/models/asr/ct2/vnpost_asr_01_20250920_ct2_fp16"
# export inference_config_path 
export CPR_MODEL_PATH="/media/nampv1/hdd/models/asr/cpr/capu"
export VAD_MODEL_PATH="/media/nampv1/hdd/models/asr/vad/snakers4_silero-vad_master"
export SEC_MODEL_PATH="/media/nampv1/hdd/models/asr/sec/"
export DEEP_FILTER_MODEL_PATH="/media/nampv1/hdd/models/asr/df/DeepFilterNet2"
export MODEL_BACKEND="transformers"
export VN_UNIGRAM_VOCAB_PATH="/home/nampv1/projects/construct-venterprise/data_construction/vn_unigram_vocab.txt"

uvicorn app.main:app --host 0.0.0.0 --port 13081 --reload