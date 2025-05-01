"""
Classes for supporting different transcription models
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SpeechToTextModel(ABC):
    """
    Abstract base class for speech to text models.
    """

    model_name: Optional[str] = None

    @abstractmethod
    def transcribe(self, audio_file_path: str) -> str:
        """
        Generates a text transcription from audio
        """
        raise NotImplementedError

@dataclass
class OpenAISpeechToTextModel(SpeechToTextModel):
    model_name: str

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes an audio file into text
        """
        from openai import AzureOpenAI

        # todo: make this Singleton
        client =  AzureOpenAI(base_url="https://aasdf/transcriptions?api-version=2024-02-15-preview",
                    api_key='asdfasdfasd',
                    api_version="2024-02-15-preview",
                )
        with open(audio_file_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model=self.model_name, file=audio
            )
            return transcription.text
