"""
Base TTS Provider Interface
Abstract class for implementing different TTS engines
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path


class TTSProvider(ABC):
    """Abstract base class for TTS providers"""

    def __init__(self, device: str = "cuda"):
        """
        Initialize TTS provider

        Args:
            device: Computation device (cuda/cpu)
        """
        self.device = device

    @abstractmethod
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
            speaker: Speaker voice identifier
            speed: Speech speed multiplier
            **kwargs: Additional provider-specific parameters

        Returns:
            Path to generated audio file
        """
        pass

    @abstractmethod
    def load_model(self, model_name: Optional[str] = None) -> Any:
        """
        Load TTS model

        Args:
            model_name: Specific model identifier

        Returns:
            Loaded model instance
        """
        pass

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages

        Returns:
            List of language codes
        """
        return ["en"]

    def get_available_voices(self) -> Dict[str, List[str]]:
        """
        Get available voices per language

        Returns:
            Dictionary mapping language codes to voice lists
        """
        return {}

    def cleanup(self):
        """Clean up resources"""
        pass
