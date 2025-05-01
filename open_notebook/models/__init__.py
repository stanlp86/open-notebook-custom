from typing import Dict, Type, Union

from open_notebook.models.embedding_models import (
    EmbeddingModel,
    OllamaEmbeddingModel,
    OpenAIEmbeddingModel,
)
from open_notebook.models.llms import (
    AnthropicLanguageModel,
    AzureChatOpenAI,
    LanguageModel,
    OllamaLanguageModel,
    OpenAILanguageModel,
)
from open_notebook.models.speech_to_text_models import (
    OpenAISpeechToTextModel,
    SpeechToTextModel,
)
from open_notebook.models.text_to_speech_models import (
    OpenAITextToSpeechModel,
    TextToSpeechModel,
)

ModelType = Union[LanguageModel, EmbeddingModel, SpeechToTextModel, TextToSpeechModel]


ProviderMap = Dict[str, Type[ModelType]]

MODEL_CLASS_MAP: Dict[str, ProviderMap] = {
    "language": {
        "ollama": OllamaLanguageModel,
        "anthropic": AnthropicLanguageModel,
        "openai": OpenAILanguageModel,
    },
    "embedding": {
        "openai": OpenAIEmbeddingModel,
        "ollama": OllamaEmbeddingModel,
    },
    "speech_to_text": {
        "openai": OpenAISpeechToTextModel,
    },
    "text_to_speech": {
        "openai": OpenAITextToSpeechModel,
    },
}

__all__ = [
    "MODEL_CLASS_MAP",
    "EmbeddingModel",
    "LanguageModel",
    "SpeechToTextModel",
    "TextToSpeechModel",
    "ModelType",
]
