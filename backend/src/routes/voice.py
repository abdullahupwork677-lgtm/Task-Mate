"""Voice API routes for Speech-to-Text (Whisper) and Text-to-Speech (TTS).

This module provides endpoints for:
- Speech-to-Text using OpenAI Whisper API
- Text-to-Speech using OpenAI TTS API
"""

import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Lazily initialized OpenAI client (for Whisper/TTS when API key is available)
_openai_client = None

def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        if not settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OpenAI API key not configured for voice features")
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech conversion.

    Attributes:
        text: Text to convert to speech (max 4096 characters)
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        speed: Speed of speech (0.25 to 4.0)
    """
    text: str = Field(..., max_length=4096, description="Text to convert to speech")
    voice: str = Field(
        default="nova",
        description="Voice to use: alloy, echo, fable, onyx, nova, shimmer"
    )
    speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="Speech speed (0.25 to 4.0)"
    )


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file (mp3, mp4, mpeg, mpga, m4a, wav, webm)"),
    current_user: str = Depends(get_current_user)
):
    """Transcribe audio to text using OpenAI Whisper API.

    Accepts audio files and returns transcribed text.

    Args:
        audio: Audio file to transcribe
        current_user: Authenticated user ID

    Returns:
        JSON with transcribed text

    Example:
        {
            "text": "Add task to buy groceries tomorrow",
            "language": "en",
            "duration": 3.5
        }

    Raises:
        HTTPException: If transcription fails
    """
    try:
        # Validate file type
        allowed_types = [
            "audio/mpeg",  # mp3
            "audio/mp4",   # m4a
            "audio/wav",   # wav
            "audio/webm",  # webm
            "audio/ogg",   # ogg
        ]

        if audio.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {audio.content_type}. Supported: mp3, mp4, wav, webm, ogg"
            )

        # Read audio file
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Create file-like object for OpenAI API
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = audio.filename or "audio.webm"

        logger.info(f"Transcribing audio for user {current_user}: {audio.filename}, size: {len(audio_bytes)} bytes")

        # Call Whisper API
        client = get_openai_client()
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

        logger.info(f"Transcription successful: '{transcription.text}' (language: {transcription.language})")

        return {
            "text": transcription.text,
            "language": transcription.language,
            "duration": transcription.duration
        }

    except Exception as e:
        logger.error(f"Transcription failed for user {current_user}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/text-to-speech")
async def text_to_speech(
    request: TextToSpeechRequest,
    current_user: str = Depends(get_current_user)
):
    """Convert text to speech using OpenAI TTS API.

    Accepts text and returns audio stream.

    Args:
        request: Text-to-speech parameters
        current_user: Authenticated user ID

    Returns:
        Audio stream (MP3 format)

    Example Request:
        {
            "text": "Task added successfully!",
            "voice": "nova",
            "speed": 1.0
        }

    Raises:
        HTTPException: If conversion fails
    """
    try:
        # Validate voice
        allowed_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if request.voice not in allowed_voices:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid voice: {request.voice}. Allowed: {', '.join(allowed_voices)}"
            )

        logger.info(f"Generating speech for user {current_user}: voice={request.voice}, speed={request.speed}, text_length={len(request.text)}")

        # Call OpenAI TTS API
        client = get_openai_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=request.voice,
            input=request.text,
            speed=request.speed
        )

        # Convert response to bytes
        audio_bytes = response.content

        logger.info(f"Speech generation successful: {len(audio_bytes)} bytes")

        # Return audio stream
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        logger.error(f"TTS failed for user {current_user}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Text-to-speech conversion failed: {str(e)}"
        )


@router.get("/voices")
async def list_voices(
    current_user: str = Depends(get_current_user)
):
    """List available TTS voices with descriptions.

    Returns:
        List of available voices with descriptions
    """
    return {
        "voices": [
            {
                "id": "alloy",
                "name": "Alloy",
                "description": "Neutral and balanced voice"
            },
            {
                "id": "echo",
                "name": "Echo",
                "description": "Male voice with warmth"
            },
            {
                "id": "fable",
                "name": "Fable",
                "description": "British accent, expressive"
            },
            {
                "id": "onyx",
                "name": "Onyx",
                "description": "Deep male voice"
            },
            {
                "id": "nova",
                "name": "Nova",
                "description": "Female voice, energetic (default)"
            },
            {
                "id": "shimmer",
                "name": "Shimmer",
                "description": "Soft female voice"
            }
        ]
    }
