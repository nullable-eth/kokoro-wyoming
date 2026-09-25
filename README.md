# Kokoro TTS Wyoming Server

High-performance GPU-accelerated Kokoro TTS server with Wyoming protocol support for Home Assistant and other applications.

## Why This Container?

Existing Kokoro Wyoming containers run on CPU, resulting in generation times of 2-4 seconds per sentence. This container leverages CUDA GPU acceleration to achieve **sub-second generation times** (~0.2-0.6s), making it suitable for real-time voice applications.

### Performance Comparison

| Implementation | Hardware | Generation Time* | Real-time Factor |
|---------------|----------|-----------------|------------------|
| CPU-only containers | Any CPU | 2-4 seconds | 0.5-1.0x |
| **This container (GPU)** | NVIDIA GPU | 0.2-0.6 seconds | **~10-30x** |

*For a typical 5-second audio output

## Features

- ✅ GPU-accelerated inference with CUDA
- ✅ Wyoming protocol for Home Assistant integration
- ✅ All 54 Kokoro v1.0 voices included
- ✅ Sub-second generation times
- ✅ **Speed control** (0.5x - 2.0x)
- ✅ **Multiple quantization levels** (fp32, fp16, int8)
- ✅ Compatible with voice conversion pipelines (RVC)

## Requirements

- Docker with NVIDIA Container Toolkit
- NVIDIA GPU with CUDA 12.x support
- ~2.5GB GPU VRAM (fp32 model)

## Quick Start

### Basic Usage (GPU, fp32 - Recommended)
```bash
docker run -d \
  --name kokoro-tts \
  --gpus all \
  -p 10210:10210 \
  nullableeth/kokoro-wyoming:latest
```

### With Speed Control
```bash
docker run -d \
  --name kokoro-tts \
  --gpus all \
  -e KOKORO_SPEED=1.3 \
  -p 10210:10210 \
  nullableeth/kokoro-wyoming:latest
```

### Docker Compose (Recommended)
```yaml
services:
  kokoro-tts:
    container_name: kokoro-tts
    image: nullableeth/kokoro-wyoming:latest
    restart: unless-stopped
    ports:
      - "10210:10210"
    environment:
      KOKORO_SPEED: "1.0"           # 0.5 - 2.0
      KOKORO_QUANTIZATION: "fp32"   # fp32 recommended for GPU
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Configuration

### Environment Variables

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `WYOMING_PORT` | `10210` | Any port | Wyoming server port |
| `KOKORO_SPEED` | `1.0` | `0.5` - `2.0` | Speech speed multiplier |
| `KOKORO_QUANTIZATION` | `fp32` | `fp32`, `fp16`, `int8` | Model quantization level |

### Quantization Levels

**IMPORTANT**: Benchmarking shows that on NVIDIA GPUs, **fp32 is fastest**. The quantized models (fp16, int8) are optimized for CPU inference and run significantly slower on GPU due to excessive CPU↔GPU memory transfers.

| Quantization | Model Size | VRAM | GPU Performance | CPU Performance | Recommendation |
|--------------|------------|------|-----------------|-----------------|----------------|
| **fp32** | 310 MB | ~2.5 GB | **Fastest (0.4s)** ✓ | Slow | **GPU: Use this** |
| **fp16** | 169 MB | ~1.5 GB | **4x slower (1.7s)** | Medium | Not recommended |
| **int8** | 88 MB | ~1 GB | **26x slower (11s)** | Fast | **CPU only** |

**Benchmark Results (RTX 4070, 5-second audio):**
- fp32: 0.44s average ⚡ **Recommended for GPU**
- fp16: 1.74s average ⚠️ Slower on GPU
- int8: 11.30s average ❌ Much slower on GPU

**Why fp32 is fastest on GPU:**
- GPUs have massive fp32 throughput
- Quantized models require excessive CPU↔GPU memory transfers
- int8/fp16 models optimized for CPU AVX-512 instructions, not CUDA

**When to use int8:**
- Running on **CPU only** (no GPU)
- Embedded/edge devices
- Limited system RAM

For GPU inference, always use **fp32**.

### Speed Control

- **Range**: 0.5x (50% slower) to 2.0x (200% faster)
- **Default**: 1.0x (normal speed)
- **Examples**:
  - `0.8` - Slower, more deliberate speech
  - `1.0` - Normal speech rate
  - `1.3` - Faster, more energetic speech
  - `1.5` - Very fast speech

**Note**: Speed affects generation time proportionally. 2.0x speed = ~50% faster generation.

## Available Voices

The container includes **54 voices** from Kokoro v1.0:

### American English (19 voices)
- **Female**: `af_alloy`, `af_aoede`, `af_bella`, `af_heart`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`, `af_river`, `af_sarah`, `af_sky`
- **Male**: `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa`

### British English (8 voices)
- **Female**: `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily`
- **Male**: `bm_daniel`, `bm_fable`, `bm_george`, `bm_lewis`

### Spanish (3 voices)
- **Female**: `ef_dora`
- **Male**: `em_alex`, `em_santa`

### French (1 voice)
- **Female**: `ff_siwis`

### Hindi (4 voices)
- **Female**: `hf_alpha`, `hf_beta`
- **Male**: `hm_omega`, `hm_psi`

### Italian (2 voices)
- **Female**: `if_sara`
- **Male**: `im_nicola`

### Japanese (5 voices)
- **Female**: `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`
- **Male**: `jm_kumo`

### Portuguese (3 voices)
- **Female**: `pf_dora`
- **Male**: `pm_alex`, `pm_santa`

### Chinese (9 voices)
- **Female**: `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`
- **Male**: `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang`

> **Voice Naming Convention**: 
> - First letter: Language (`a`=American, `b`=British, `e`=Spanish, `f`=French, `h`=Hindi, `i`=Italian, `j`=Japanese, `p`=Portuguese, `z`=Chinese)
> - Second letter: Gender (`f`=Female, `m`=Male)
> - Rest: Voice name

## Home Assistant Integration

### Add to configuration.yaml
```yaml
tts:
  - platform: wyoming
    host: 192.168.1.100  # Your Docker host IP
    port: 10210
    voice: af_sky  # Default voice
```

### Test in Home Assistant
```yaml
service: tts.speak
data:
  entity_id: media_player.living_room
  message: "Hello from Kokoro TTS"
  options:
    voice: af_bella  # Choose any of the 54 voices
```

## Performance Examples

**GPU (RTX 4070) - Always use fp32:**

| Speed | Generation Time | VRAM Usage | Use Case |
|-------|-----------------|------------|----------|
| 1.0x | 0.44s | 2.5 GB | Default, best quality |
| 1.3x | 0.34s | 2.5 GB | Faster speech |
| 1.5x | 0.29s | 2.5 GB | Very fast speech |
| 2.0x | 0.22s | 2.5 GB | Maximum speed |

*For ~5 second audio output with fp32 quantization*

**CPU Mode (use int8):**
```yaml
environment:
  KOKORO_QUANTIZATION: "int8"  # Optimized for CPU
# Remove the deploy.resources.reservations section
```

## Command Line Usage

Using Wyoming client tools:
```bash
# Install wyoming client
pip install wyoming

# Generate speech
echo "Hello world" | wyoming-client \
  --host localhost \
  --port 10210 \
  --voice af_sky \
  --output output.wav
```

## Advanced Usage

### Chain with RVC Voice Conversion

Kokoro can be chained with RVC (Retrieval-based Voice Conversion) for custom voices:
```yaml
services:
  kokoro-tts:
    image: nullableeth/kokoro-wyoming:latest
    ports:
      - "10210:10210"
    environment:
      KOKORO_QUANTIZATION: "fp32"  # Fast GPU inference
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  rvc-converter:
    image: nullableeth/rvc-wyoming:latest
    ports:
      - "10900:10900"
    environment:
      TTS_HOST: "kokoro-tts"
      TTS_PORT: "10210"
      TTS_VOICE: "af_sky"
      MODEL_NAME: "your_model.pth"
    volumes:
      - ./rvc_models:/models:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Point Home Assistant or clients to port `10900` to use RVC-converted voices.

## Troubleshooting

### Container starts but no GPU acceleration

Check if GPU is accessible:
```bash
docker exec kokoro-tts python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

Should output: `CUDA available: True`

### Poor performance (>2 seconds per generation)

1. **Verify you're using fp32**: `docker logs kokoro-tts | grep "Loading Kokoro"`
   - Should show: `Loading Kokoro model (fp32, speed: 1.0x)...`
2. **Check for excessive Memcpy operations**: `docker logs kokoro-tts | grep Memcpy`
   - fp32 should show ~39 nodes
   - fp16/int8 show 100s of nodes = slow!
3. Verify GPU is being used (see above)
4. Check NVIDIA Container Toolkit is installed:
```bash
   docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Using fp16 or int8 makes it slower

This is **expected behavior**. The quantized models are optimized for CPU inference and run slower on GPU due to excessive memory transfers. Always use **fp32 for GPU**.

### Invalid quantization error

Container logs show: `Invalid KOKORO_QUANTIZATION 'xyz'`

**Solution**: Use only `fp32`, `fp16`, or `int8`

### Speed parameter out of range

Container fails with: `KOKORO_SPEED must be between 0.5 and 2.0`

**Solution**: Set `KOKORO_SPEED` between 0.5 and 2.0

### Connection refused

Verify port mapping and firewall settings:
```bash
docker logs kokoro-tts | grep "Starting server"
```

## Technical Details

### Architecture

- **Base Image**: `pytorch/pytorch:2.10.0-cuda12.8-cudnn9-runtime`
- **Model**: Kokoro v1.0 (82M parameters)
- **Runtime**: ONNX Runtime 1.23.2 with GPU support
- **Protocol**: Wyoming for Home Assistant compatibility

### GPU Acceleration

The container uses ONNX Runtime with CUDAExecutionProvider for GPU acceleration. Required CUDA libraries are bundled in the image via pip packages (nvidia-cublas, nvidia-cudnn, etc.).

**Quantization Performance Note**: The int8 and fp16 models generate excessive CPU↔GPU memory transfers (550+ Memcpy operations vs 39 for fp32), making them significantly slower on GPU. These quantized models are optimized for CPU inference with AVX-512 instructions, not CUDA.

## Building From Source
```bash
git clone <your-repo>
cd kokoro-wyoming
docker build -t kokoro-wyoming:latest .
```

## License

This container packages:
- Kokoro TTS (Model license: see [Kokoro GitHub](https://github.com/hexgrad/Kokoro-TTS))
- Wyoming Protocol (MIT)
- ONNX Runtime (MIT)

## Credits

- **Kokoro TTS**: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- **Kokoro ONNX**: [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)
- **Wyoming Protocol**: [rhasspy/wyoming](https://github.com/rhasspy/wyoming)
- **ONNX Runtime**: Microsoft

## Support

For issues specific to this container, please open an issue on GitHub.
For Kokoro model issues, see the [official Kokoro repository](https://github.com/hexgrad/Kokoro-TTS).
---

## Provenance

The original build context for this image was lost (built directly on the
media server, pushed straight to Docker Hub). This repository was
reconstructed on 2026-09-25 from the running image:

- source: `nullableeth/kokoro-wyoming:latest` (image config `sha256:d7323a529c93ca0afe96824f8bd05cf62ee7188202d91be963613e40981b0031`)
- `src/` extracted verbatim from `/app/wrapper.py` in the running container
- Dockerfile rebuilt from the image-config layer history, with previously
  unpinned dependencies pinned to the versions the shipped image contains

CI publishes to `ghcr.io/nullable-eth/kokoro-wyoming` (latest + sha tags on main,
version tags on `v*`).
