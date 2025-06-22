import os
from dotenv import load_dotenv
from io import BytesIO
import requests
from elevenlabs.client import ElevenLabs

load_dotenv()

def get_transcription(audio_url: str, model_id: str = "scribe_v1", language_code: str = "eng", diarize: bool = True, tag_audio_events: bool = True) -> str:
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVEN_LABS_API_KEY"),
    )

    response = requests.get(audio_url)
    audio_data = BytesIO(response.content)

    transcription = elevenlabs.speech_to_text.convert(
        file=audio_data,
        model_id=model_id, # Model to use, for now only "scribe_v1" is supported
        tag_audio_events=tag_audio_events, # Tag audio events like laughter, applause, etc.
        language_code=language_code, # Language of the audio file. If set to None, the model will detect the language automatically.
        diarize=diarize, # Whether to annotate who is speaking
    )

    return transcription
