"""
Voice Synthesis Module with Multi-Provider Support
Supports three TTS providers: Coqui TTS, Fish Audio SDK, and Fish Speech
Generates natural-sounding speech from text using various TTS engines
"""

import os
import torch
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
import logging
from .providers import TTSProvider, CoquiTTSProvider, FishSpeechProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fish Audio SDK imports (optional)
try:
    from fishaudio import FishAudio, AsyncFishAudio
    from fishaudio.types import TTSConfig, Prosody
    from fishaudio.exceptions import (
        AuthenticationError,
        RateLimitError,
        ValidationError,
        FishAudioError
    )
    FISH_AUDIO_AVAILABLE = True
    logger.info("✅ Fish Audio SDK available")
except ImportError:
    FISH_AUDIO_AVAILABLE = False
    logger.warning("⚠️  Fish Audio SDK not installed. Only Coqui TTS and Fish Speech available.")


class FishAudioProvider(TTSProvider):
    """Fish Audio SDK TTS provider with cloud-based voice cloning"""

    # Language support mapping
    LANGUAGE_SUPPORT = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "hi": "Hindi",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "pt": "Portuguese",
        "ru": "Russian",
        "ar": "Arabic",
        "it": "Italian"
    }

    def __init__(self, device: str = "cuda", api_key: Optional[str] = None):
        """
        Initialize Fish Audio synthesizer

        Args:
            device: Computation device (not used for cloud API)
            api_key: Fish Audio API key (or use FISH_API_KEY env var)
        """
        super().__init__(device)

        if not FISH_AUDIO_AVAILABLE:
            raise ImportError(
                "Fish Audio SDK not installed. Install with: pip install fish-audio-sdk"
            )

        self.api_key = api_key or os.getenv("FISH_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Fish Audio API key required. Set FISH_API_KEY env var or pass api_key parameter. "
                "Get your key at: https://fish.audio/app/api-keys"
            )

        self.client = FishAudio(api_key=self.api_key)
        logger.info("✅ Fish Audio client initialized")

    def load_model(self, model_name: Optional[str] = None) -> Any:
        """Fish Audio models are cloud-based, no local loading needed"""
        return True

    def synthesize(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0,
        volume: int = 0,
        audio_format: str = "wav",
        **kwargs
    ) -> str:
        """
        Synthesize speech using Fish Audio

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Target language code
            speaker: Fish Audio voice reference ID (reference_id)
            speed: Speech speed multiplier (0.5 - 2.0)
            volume: Volume adjustment in dB (-20 to 20)
            audio_format: Output format ('wav' or 'mp3')

        Returns:
            Path to generated audio file
        """
        try:
            if not text or not text.strip():
                raise ValueError("Empty text provided for synthesis")

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"🐟 Fish Audio: Synthesizing speech for '{language}'")
            logger.info(f"   Text length: {len(text)} characters")
            logger.info(f"   Speed: {speed}x, Volume: {volume}dB")

            # Configure TTS settings
            config = TTSConfig(
                format=audio_format,
                prosody=Prosody(speed=speed, volume=volume),
                latency="balanced"
            )

            # Generate speech
            if speaker:  # speaker is the reference_id for Fish Audio
                logger.info(f"   Using voice reference: {speaker}")
                audio_data = self.client.tts.convert(
                    text=text,
                    reference_id=speaker,
                    config=config
                )
            else:
                # Use default voice for language
                audio_data = self.client.tts.convert(
                    text=text,
                    config=config
                )

            # Save audio file
            with open(output_path, 'wb') as f:
                f.write(audio_data)

            if not Path(output_path).exists():
                raise FileNotFoundError("Fish Audio failed to generate audio file")

            file_size = Path(output_path).stat().st_size / 1024  # KB
            logger.info(f"✅ Fish Audio synthesis complete")
            logger.info(f"   Output: {Path(output_path).name}")
            logger.info(f"   Size: {file_size:.1f} KB")

            return output_path

        except AuthenticationError as e:
            logger.error(f"❌ Fish Audio authentication failed: {e}")
            raise RuntimeError(
                "Fish Audio API key invalid. Get your key at: https://fish.audio/app/api-keys"
            )
        except RateLimitError as e:
            logger.error(f"❌ Fish Audio rate limit exceeded: {e}")
            raise RuntimeError("Fish Audio rate limit exceeded. Please try again later.")
        except ValidationError as e:
            logger.error(f"❌ Fish Audio validation error: {e}")
            raise RuntimeError(f"Invalid parameters for Fish Audio: {e}")
        except FishAudioError as e:
            logger.error(f"❌ Fish Audio error: {e}")
            raise RuntimeError(f"Fish Audio TTS error: {e}")
        except Exception as e:
            logger.error(f"❌ Fish Audio synthesis failed: {e}")
            raise RuntimeError(f"Speech synthesis error: {e}")

    def get_account_info(self) -> dict:
        """Get Fish Audio account credits and usage"""
        try:
            credits = self.client.account.get_credits()
            return {
                "provider": "fish_audio",
                "credits": credits,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {"provider": "fish_audio", "status": "error", "error": str(e)}

    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return list(self.LANGUAGE_SUPPORT.keys())

    def get_available_voices(self) -> Dict[str, List[str]]:
        """Get available voices for Fish Audio"""
        return {"fish_audio": ["default"]}

    def cleanup(self):
        """Clean up Fish Audio resources"""
        logger.info("Fish Audio provider cleaned up")


class VoiceSynthesizer:
    """
    Professional TTS with multi-provider support

    Supported Providers:
    - Coqui TTS: Local multi-language TTS
    - Fish Audio SDK: Cloud-based TTS with API key
    - Fish Speech: Self-hosted SOTA TTS with voice cloning and emotion support
    """

    PROVIDERS = {
        "coqui": CoquiTTSProvider,
        "fish_audio": FishAudioProvider,
        "fish_speech": FishSpeechProvider
    }

    def __init__(
        self,
        provider: Literal["auto", "coqui", "fish_audio", "fish_speech"] = "auto",
        device: Optional[str] = None,
        **provider_kwargs
    ):
        """
        Initialize TTS synthesizer with specified provider

        Args:
            provider: TTS provider to use (auto, coqui, fish_audio, fish_speech)
            device: Computation device (cuda/cpu)
            **provider_kwargs: Provider-specific initialization parameters
                Fish Audio: api_key
                Fish Speech: api_url, model, compile_mode, etc.
        """
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.provider_name = provider.lower()

        # Auto-select provider
        if self.provider_name == "auto":
            self.provider_name = self._auto_select_provider(provider_kwargs)
            logger.info(f"Auto-selected provider: {self.provider_name}")

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

    def _auto_select_provider(self, provider_kwargs: Dict) -> str:
        """
        Auto-select best available TTS provider

        Priority:
        1. Fish Audio SDK (if API key available)
        2. Fish Speech (if API URL configured)
        3. Coqui TTS (fallback)
        """
        # Check Fish Audio SDK availability
        if FISH_AUDIO_AVAILABLE:
            api_key = provider_kwargs.get("api_key") or os.getenv("FISH_API_KEY")
            if api_key:
                logger.info("🐟 Fish Audio SDK available with API key")
                return "fish_audio"

        # Check Fish Speech availability
        fish_speech_url = provider_kwargs.get("api_url") or os.getenv("FISH_SPEECH_API_URL")
        if fish_speech_url:
            logger.info("🐟 Fish Speech API URL configured")
            return "fish_speech"

        # Fallback to Coqui
        logger.info("🎤 No cloud providers configured, using Coqui TTS")
        return "coqui"

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
            speaker: Speaker voice (provider-specific)
            speed: Speech speed multiplier
            **kwargs: Provider-specific parameters
                Fish Audio: volume, audio_format, reference_id
                Fish Speech: emotion, reference_audio, reference_text, streaming
                Coqui: (none)

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

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about active provider"""
        info = {
            "provider": self.provider_name,
            "device": self.device
        }

        # Add provider-specific info
        if self.provider_name == "fish_audio" and isinstance(self.provider, FishAudioProvider):
            info["features"] = ["voice_cloning", "multi_language", "cloud_based", "high_quality"]
            info["account"] = self.provider.get_account_info()
        elif self.provider_name == "fish_speech" and isinstance(self.provider, FishSpeechProvider):
            info["features"] = ["voice_cloning", "emotion_synthesis", "streaming", "multilingual", "self_hosted"]
            info["model"] = self.provider.model
            info["api_url"] = self.provider.api_url
        elif self.provider_name == "coqui":
            info["features"] = ["multi_language", "local_processing", "offline"]

        return info

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
_synthesizer_lock = threading.Lock()


def get_synthesizer(provider: Optional[str] = None, **kwargs) -> VoiceSynthesizer:
    """
    Get or create global synthesizer instance (thread-safe)

    Args:
        provider: TTS provider to use (auto, coqui, fish_audio, fish_speech)
        **kwargs: Provider-specific parameters

    Returns:
        VoiceSynthesizer instance
    """
    global _synthesizer, _current_provider

    # Get provider from environment if not specified
    if provider is None:
        provider = os.getenv("TTS_PROVIDER", "auto")

    # Quick check without lock for performance
    if _synthesizer is not None and _current_provider == provider:
        return _synthesizer

    # Thread-safe initialization
    with _synthesizer_lock:
        # Re-check inside lock to handle race condition
        if _synthesizer is None or _current_provider != provider:
            if _synthesizer is not None:
                _synthesizer.cleanup()

            # Get Fish Audio config from environment
            if provider in ("auto", "fish_audio"):
                kwargs.setdefault("api_key", os.getenv("FISH_API_KEY"))

            # Get Fish Speech config from environment
            if provider in ("auto", "fish_speech"):
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
    provider: Optional[str] = None,
    **kwargs
) -> str:
    """
    Convenience function for speech synthesis

    Args:
        text: Text to synthesize
        output_path: Output file path
        language: Target language
        provider: Override default provider (auto, coqui, fish_audio, fish_speech)
        **kwargs: Additional synthesis parameters

    Returns:
        Path to generated audio
    """
    synthesizer = get_synthesizer(provider=provider)
    return synthesizer.synthesize(text, output_path, language, **kwargs)
