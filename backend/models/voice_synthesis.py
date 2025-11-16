"""
Voice Synthesis Module with Multi-Provider Support
Generates natural-sounding speech from text using various TTS engines
"""

import os
import torch
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from .providers import TTSProvider, CoquiTTSProvider, FishSpeechProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceSynthesizer:
    """
    Professional TTS with multi-provider support

    Supported Providers:
    - Coqui TTS: Original multi-language TTS
    - Fish Speech: SOTA TTS with voice cloning and emotion support
    """

    PROVIDERS = {
        "coqui": CoquiTTSProvider,
        "fish_speech": FishSpeechProvider
    }

    def __init__(
        self,
        provider: str = "coqui",
        device: Optional[str] = None,
        **provider_kwargs
    ):
        """
        Initialize TTS synthesizer with specified provider

        Args:
            provider: TTS provider to use (coqui, fish_speech)
            device: Computation device (cuda/cpu)
            **provider_kwargs: Provider-specific initialization parameters
        """
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.provider_name = provider.lower()

        # Validate provider
        if self.provider_name not in self.PROVIDERS:
            raise ValueError(
                f"Unknown TTS provider: {provider}. "
                f"Available: {list(self.PROVIDERS.keys())}"
            )

        # Initialize provider
        provider_class = self.PROVIDERS[self.provider_name]
        self.provider: TTSProvider = provider_class(device=device, **provider_kwargs)

        logger.info(f"Initialized VoiceSynthesizer with {self.provider_name} provider on {self.device}")

    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> str:
        """
        Synthesize speech from text

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Target language code
            speaker: Speaker voice (if multi-speaker model)
            speed: Speech speed multiplier
            **kwargs: Provider-specific parameters
                Fish Speech:
                    - emotion: Emotion marker (angry, sad, excited, etc.)
                    - reference_audio: Path to reference audio for voice cloning
                    - reference_text: Transcript of reference audio
                    - streaming: Enable streaming mode

        Returns:
            Path to generated audio file
        """
        return self.provider.synthesize(
            text=text,
            output_path=output_path,
            language=language,
            speaker=speaker,
            speed=speed,
            **kwargs
        )

    def load_model(self, model_name: Optional[str] = None):
        """
        Load TTS model

        Args:
            model_name: Specific model to load
        """
        return self.provider.load_model(model_name)

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages for current provider

        Returns:
            List of language codes
        """
        return self.provider.get_supported_languages()

    def get_available_voices(self) -> Dict[str, List[str]]:
        """
        Get available voices for current provider

        Returns:
            Dictionary mapping language codes to voice lists
        """
        return self.provider.get_available_voices()

    def cleanup(self):
        """Clean up provider resources"""
        self.provider.cleanup()

    # Fish Speech specific methods
    def add_reference_voice(
        self,
        voice_id: str,
        audio_path: str,
        text: Optional[str] = None
    ) -> bool:
        """
        Add a reference voice for voice cloning (Fish Speech only)

        Args:
            voice_id: Unique identifier for the voice
            audio_path: Path to reference audio file
            text: Optional transcript of the reference audio

        Returns:
            True if successful
        """
        if isinstance(self.provider, FishSpeechProvider):
            return self.provider.add_reference_voice(voice_id, audio_path, text)
        else:
            logger.warning(f"Reference voice not supported by {self.provider_name}")
            return False

    def list_reference_voices(self) -> List[Dict[str, Any]]:
        """
        List available reference voices (Fish Speech only)

        Returns:
            List of reference voice information
        """
        if isinstance(self.provider, FishSpeechProvider):
            return self.provider.list_reference_voices()
        else:
            logger.warning(f"Reference voices not supported by {self.provider_name}")
            return []

    def get_available_emotions(self) -> List[str]:
        """
        Get available emotion markers (Fish Speech only)

        Returns:
            List of emotion markers
        """
        if isinstance(self.provider, FishSpeechProvider):
            return self.provider.get_available_emotions()
        else:
            logger.warning(f"Emotion markers not supported by {self.provider_name}")
            return []


# Global instance
_synthesizer = None
_current_provider = None


def get_synthesizer(provider: Optional[str] = None, **kwargs) -> VoiceSynthesizer:
    """
    Get or create global synthesizer instance

    Args:
        provider: TTS provider to use
        **kwargs: Provider-specific parameters

    Returns:
        VoiceSynthesizer instance
    """
    global _synthesizer, _current_provider

    # Get provider from environment if not specified
    if provider is None:
        provider = os.getenv("TTS_PROVIDER", "coqui")

    # Recreate if provider changed or doesn't exist
    if _synthesizer is None or _current_provider != provider:
        if _synthesizer is not None:
            _synthesizer.cleanup()

        # Get Fish Speech config from environment if using Fish Speech
        if provider == "fish_speech":
            kwargs.setdefault("api_url", os.getenv("FISH_SPEECH_API_URL", "http://localhost:8080"))
            kwargs.setdefault("model", os.getenv("FISH_SPEECH_MODEL", "s1-mini"))
            kwargs.setdefault("compile_mode", os.getenv("FISH_SPEECH_COMPILE", "False").lower() == "true")
            kwargs.setdefault("max_new_tokens", int(os.getenv("FISH_SPEECH_MAX_NEW_TOKENS", "1024")))
            kwargs.setdefault("top_p", float(os.getenv("FISH_SPEECH_TOP_P", "0.7")))
            kwargs.setdefault("temperature", float(os.getenv("FISH_SPEECH_TEMPERATURE", "0.7")))
            kwargs.setdefault("repetition_penalty", float(os.getenv("FISH_SPEECH_REPETITION_PENALTY", "1.2")))

        _synthesizer = VoiceSynthesizer(provider=provider, **kwargs)
        _current_provider = provider

    return _synthesizer


def synthesize_speech(
    text: str,
    output_path: str,
    language: str = "en",
    **kwargs
) -> str:
    """
    Convenience function for speech synthesis

    Args:
        text: Text to synthesize
        output_path: Output file path
        language: Target language
        **kwargs: Additional synthesis parameters

    Returns:
        Path to generated audio
    """
    synthesizer = get_synthesizer()
    return synthesizer.synthesize(text, output_path, language, **kwargs)
