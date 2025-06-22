from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.speech_to_text import get_transcription

router = APIRouter(prefix="/api/v1", tags=["audio-transcription"])

# Request schema for the transcription endpoint
class TranscriptionRequest(BaseModel):
    audio_url: str
    model_id: str = "scribe_v1"
    language_code: str = "eng"
    diarize: bool = True
    tag_audio_events: bool = True

@router.post("/transcribe")
async def get_transcript(request: TranscriptionRequest):

    try:
        # get_transcription is a synchronous function, so we call it directly (without await)
        transcription = get_transcription(
            audio_url=request.audio_url,
            model_id=request.model_id,
            language_code=request.language_code,
            diarize=request.diarize,
            tag_audio_events=request.tag_audio_events,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return transcription
    
