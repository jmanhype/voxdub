"""
Security Utilities
Secure file handling, validation, and sanitization
"""

import magic
import re
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

# Allowed MIME types for audio files
ALLOWED_AUDIO_MIMES = {
    'audio/wav',
    'audio/x-wav',
    'audio/mpeg',
    'audio/mp3',
    'audio/flac',
    'audio/x-flac',
    'audio/ogg',
    'audio/vorbis',
    'audio/x-vorbis+ogg'
}

# Maximum file sizes (in bytes)
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_REFERENCE_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for storage
    """
    # Remove path components
    filename = Path(filename).name

    # Remove any non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Remove multiple dots
    filename = re.sub(r'\.+', '.', filename)

    # Truncate to reasonable length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename


def generate_secure_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate a secure random filename preserving extension

    Args:
        original_filename: Original filename to extract extension from
        prefix: Optional prefix for the filename

    Returns:
        Secure random filename
    """
    # Get extension from sanitized filename
    sanitized = sanitize_filename(original_filename)
    ext = Path(sanitized).suffix if sanitized else '.wav'

    # Generate random filename
    random_name = str(uuid.uuid4())

    if prefix:
        # Sanitize prefix
        safe_prefix = re.sub(r'[^\w-]', '', prefix)
        return f"{safe_prefix}_{random_name}{ext}"

    return f"{random_name}{ext}"


async def validate_audio_file(
    file: UploadFile,
    max_size: int = MAX_AUDIO_SIZE
) -> Tuple[bytes, str]:
    """
    Validate uploaded audio file for security

    Args:
        file: Uploaded file
        max_size: Maximum allowed file size in bytes

    Returns:
        Tuple of (file_content, mime_type)

    Raises:
        HTTPException: If validation fails
    """
    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )

    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB"
        )

    # Detect MIME type from content
    try:
        mime = magic.from_buffer(content, mime=True)
    except Exception as e:
        logger.error(f"MIME type detection failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Unable to detect file type"
        )

    # Validate MIME type
    if mime not in ALLOWED_AUDIO_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: WAV, MP3, FLAC, OGG. Detected: {mime}"
        )

    logger.info(f"Validated audio file: {file.filename} ({file_size} bytes, {mime})")

    return content, mime


def generate_file_hash(content: bytes) -> str:
    """
    Generate SHA256 hash of file content

    Args:
        content: File content bytes

    Returns:
        Hex digest of SHA256 hash
    """
    return hashlib.sha256(content).hexdigest()


def sanitize_voice_id(voice_id: str) -> str:
    """
    Sanitize voice ID to prevent injection attacks

    Args:
        voice_id: User-provided voice ID

    Returns:
        Sanitized voice ID

    Raises:
        HTTPException: If voice_id is invalid
    """
    # Remove any non-alphanumeric characters except hyphens and underscores
    sanitized = re.sub(r'[^\w-]', '', voice_id)

    # Ensure it's not empty
    if not sanitized or len(sanitized) < 3:
        raise HTTPException(
            status_code=400,
            detail="Voice ID must be at least 3 alphanumeric characters"
        )

    # Limit length
    if len(sanitized) > 64:
        raise HTTPException(
            status_code=400,
            detail="Voice ID must not exceed 64 characters"
        )

    return sanitized


def validate_text_input(text: str, max_length: int = 5000) -> str:
    """
    Validate and sanitize text input

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Validated text

    Raises:
        HTTPException: If validation fails
    """
    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )

    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum: {max_length} characters"
        )

    return text.strip()


def validate_language_code(language: str, supported_languages: list) -> str:
    """
    Validate language code against supported languages

    Args:
        language: Language code
        supported_languages: List of supported language codes

    Returns:
        Validated language code

    Raises:
        HTTPException: If language not supported
    """
    language = language.lower().strip()

    if language not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}"
        )

    return language


def validate_emotion(emotion: Optional[str], available_emotions: list) -> Optional[str]:
    """
    Validate emotion marker

    Args:
        emotion: Emotion marker
        available_emotions: List of available emotions

    Returns:
        Validated emotion or None

    Raises:
        HTTPException: If emotion not supported
    """
    if emotion is None:
        return None

    emotion = emotion.lower().strip()

    if emotion not in available_emotions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported emotion: {emotion}. Available: {', '.join(available_emotions)}"
        )

    return emotion
