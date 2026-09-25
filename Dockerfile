# syntax=docker/dockerfile:1
# Recovered 2026-09-25 from nullableeth/kokoro-wyoming:latest image-config
# history after the original build context (built on the media server) was
# lost. Faithful to the shipped image; unpinned deps pinned to the versions
# that image actually contains.
#
# The pytorch base is here for one reason: onnxruntime-gpu needs cuDNN/cuBLAS,
# and this base ships them as pip nvidia-* libs (see LD_LIBRARY_PATH below).
FROM pytorch/pytorch:2.10.0-cuda12.8-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# NOTE (known hazard, fixed on the improvements branch): kokoro-onnx depends on
# CPU onnxruntime, so this installs BOTH wheels into the same module dir; the
# GPU wheel happens to win at import time in this build.
RUN pip install --no-cache-dir --break-system-packages \
    kokoro-onnx==0.5.0 \
    onnxruntime-gpu==1.23.2 \
    wyoming==1.8.0 \
    soundfile \
    numpy

# onnxruntime-gpu resolves cuDNN/cuBLAS from the base image's pip nvidia libs
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/lib/python3.12/dist-packages/nvidia/cublas/lib:/usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.12/dist-packages/nvidia/cuda_runtime/lib:/usr/local/lib/python3.12/dist-packages/nvidia/curand/lib:/usr/local/lib/python3.12/dist-packages/nvidia/cufft/lib

RUN mkdir -p /app/kokoro_models && cd /app/kokoro_models && \
    echo "Downloading fp32 model (310MB)..." && \
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx && \
    echo "Downloading fp16 model (169MB)..." && \
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.fp16.onnx && \
    echo "Downloading int8 model (88MB)..." && \
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx && \
    echo "Downloading voices..." && \
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin && \
    mv voices-v1.0.bin voices.npy

COPY src/kokoro_wyoming.py /app/wrapper.py

ENV WYOMING_PORT=10210 \
    KOKORO_SPEED=1.0 \
    KOKORO_QUANTIZATION=fp32 \
    ONNX_PROVIDER=CUDAExecutionProvider \
    ORT_LOG_LEVEL=3

EXPOSE 10210
ENTRYPOINT ["python3", "/app/wrapper.py"]
