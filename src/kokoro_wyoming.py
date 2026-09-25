#!/usr/bin/env python3
import asyncio
import logging
import os
import numpy as np
from functools import partial

from wyoming.info import Attribution, Info, TtsProgram, TtsVoice, Describe
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.tts import Synthesize
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event

_LOGGER = logging.getLogger(__name__)

WYOMING_PORT = os.environ.get('WYOMING_PORT', '10210')
KOKORO_SPEED = float(os.environ.get('KOKORO_SPEED', '1.0'))
KOKORO_QUANTIZATION = os.environ.get('KOKORO_QUANTIZATION', 'fp32')

class KokoroEventHandler(AsyncEventHandler):
    """Event handler for Kokoro TTS."""
    
    def __init__(
        self,
        wyoming_info: Info,
        kokoro_model,
        available_voices: list,
        speed: float,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.wyoming_info_event = wyoming_info.event()
        self.kokoro = kokoro_model
        self.available_voices = available_voices
        self.speed = speed

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_event)
            return True
        
        if Synthesize.is_type(event.type):
            synthesize = Synthesize.from_event(event)
            text = synthesize.text
            
            # Get voice from request, default to first available if not specified
            voice = synthesize.voice.name if synthesize.voice else self.available_voices[0]
            
            _LOGGER.info(f"Synthesizing with voice '{voice}' at {self.speed}x speed: '{text}'")
            
            # Generate with Kokoro (with speed control)
            samples, sample_rate = self.kokoro.create(text, voice=voice, speed=self.speed)
            
            # Convert to int16
            if samples.dtype != np.int16:
                samples = (samples * 32767).astype(np.int16)
            
            # Send audio with AudioStart first
            await self.write_event(AudioStart(rate=sample_rate, width=2, channels=1).event())
            
            chunk_size = 8192
            for i in range(0, len(samples), chunk_size):
                chunk = samples[i:i+chunk_size]
                await self.write_event(
                    AudioChunk(audio=chunk.tobytes(), rate=sample_rate, width=2, channels=1).event()
                )
            
            await self.write_event(AudioStop().event())
            return True
        
        return True

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Validate speed
    if KOKORO_SPEED < 0.5 or KOKORO_SPEED > 2.0:
        _LOGGER.error(f"KOKORO_SPEED must be between 0.5 and 2.0, got {KOKORO_SPEED}")
        return
    
    # Validate and select model file based on quantization
    quantization_map = {
        'fp32': 'kokoro-v1.0.onnx',
        'fp16': 'kokoro-v1.0.fp16.onnx',
        'int8': 'kokoro-v1.0.int8.onnx',
    }
    
    if KOKORO_QUANTIZATION not in quantization_map:
        _LOGGER.error(f"Invalid KOKORO_QUANTIZATION '{KOKORO_QUANTIZATION}'. Must be one of: {list(quantization_map.keys())}")
        return
    
    model_file = quantization_map[KOKORO_QUANTIZATION]
    model_path = f"/app/kokoro_models/{model_file}"
    
    if not os.path.exists(model_path):
        _LOGGER.error(f"Model file not found: {model_path}")
        return
    
    # Always use CUDA
    os.environ['ONNX_PROVIDER'] = 'CUDAExecutionProvider'
    
    # Load Kokoro ONCE at startup
    _LOGGER.info(f"Loading Kokoro model ({KOKORO_QUANTIZATION}, speed: {KOKORO_SPEED}x)...")
    from kokoro_onnx import Kokoro
    kokoro = Kokoro(model_path, "/app/kokoro_models/voices.npy")
    
    # Get available voices - it's an npz file, use keys()
    voices_npz = np.load("/app/kokoro_models/voices.npy", allow_pickle=True)
    available_voices = list(voices_npz.keys())
    voices_npz.close()
    
    _LOGGER.info(f"✓ Kokoro loaded with {len(available_voices)} voices")
    
    # Build Wyoming info with ALL available voices
    wyoming_info = Info(
        tts=[
            TtsProgram(
                name="kokoro",
                version="1.0",
                description=f"Kokoro TTS ({KOKORO_QUANTIZATION})",
                attribution=Attribution(name="Kokoro", url="https://huggingface.co/hexgrad/Kokoro-82M"),
                installed=True,
                voices=[
                    TtsVoice(
                        name=voice,
                        description=f"Kokoro voice: {voice}",
                        attribution=Attribution(name="Kokoro", url=""),
                        installed=True,
                        languages=["en_US"],
                        version="1.0",
                    )
                    for voice in available_voices
                ],
            )
        ],
    )
    
    wyoming_uri = f"tcp://0.0.0.0:{WYOMING_PORT}"
    _LOGGER.info(f"Starting server on {wyoming_uri}")
    
    server = AsyncServer.from_uri(wyoming_uri)
    await server.run(partial(KokoroEventHandler, wyoming_info, kokoro, available_voices, KOKORO_SPEED))

if __name__ == "__main__":
    asyncio.run(main())
