"""
Classes for supporting different language models
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama.chat_models import ChatOllama
from langchain_openai import AzureChatOpenAI

# from pydantic import SecretStr

# future: is there a value on returning langchain specific models?


@dataclass
class LanguageModel(ABC):
    """
    Abstract base class for language models.
    """

    model_name: Optional[str] = None
    max_tokens: Optional[int] = 850
    temperature: Optional[float] = 1.0
    streaming: bool = True
    top_p: Optional[float] = 0.9
    kwargs: Dict[str, Any] = field(default_factory=dict)
    json: bool = False

    @abstractmethod
    def to_langchain(self) -> BaseChatModel:
        """
        Convert the language model to a LangChain chat model.
        """
        raise NotImplementedError


@dataclass
class AnthropicLanguageModel(LanguageModel):
    """
    Language model that uses the Anthropic chat model.
    """

    model_name: str

    def to_langchain(self) -> ChatAnthropic:
        """
        Convert the language model to a LangChain chat model.
        """
        return ChatAnthropic(  # type: ignore[call-arg]
            anthropic_api_url="https://anthropic",
            # model_name=self.model_name,
            model_name="claude-3-7-sonnet-20250219",
            api_key="asdfas",
            max_tokens_to_sample=self.max_tokens or 850,
            model_kwargs=self.kwargs,
            streaming=False,
            timeout=120,
            top_p=self.top_p,
            temperature=self.temperature or 0.5,
        )

@dataclass
class OllamaLanguageModel(LanguageModel):
    """
    Language model that uses the Ollama chat model.
    """

    model_name: str
    base_url: str = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
    max_tokens: Optional[int] = 650
    json: bool = False

    def to_langchain(self) -> ChatOllama:
        """
        Convert the language model to a LangChain chat model.
        """
        return ChatOllama(
            # api_key="ollama",
            model=self.model_name,
            base_url=self.base_url,
            # keep_alive="10m",
            num_predict=self.max_tokens,
            temperature=self.temperature or 0.5,
            verbose=True,
            top_p=self.top_p,
        )

@dataclass
class OpenAILanguageModel(LanguageModel):
    """
    Language model that uses the OpenAI chat model.
    """

    model_name: str

    def to_langchain(self) -> AzureChatOpenAI:
        """
        Convert the language model to a LangChain chat model.
        """

        kwargs = self.kwargs.copy()  # Make a copy to avoid modifying the original
        if self.json:
            kwargs["response_format"] = {"type": "json_object"}

        return AzureChatOpenAI(
            api_key="asdf",
            azure_endpoint="https://asdfasdf",
            openai_api_version="2023-07-01-preview",
            azure_deployment="gpt-4-turbo",
            model=self.model_name,
            temperature=self.temperature or 0.5,
            streaming=self.streaming,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            model_kwargs=kwargs,
        )
