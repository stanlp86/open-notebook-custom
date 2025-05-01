"""
Classes for supporting different embedding models
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import requests

# todo: add support for multiple embeddings (array)


@dataclass
class EmbeddingModel(ABC):
    """
    Abstract base class for language models.
    """

    model_name: Optional[str] = None

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generates an embedding
        """
        raise NotImplementedError


@dataclass
class OpenAIEmbeddingModel(EmbeddingModel):
    model_name: str

    def embed(self, text: str) -> List[float]:
        # from openai import OpenAI
        from langchain_openai import AzureOpenAIEmbeddings

        """
        Embeds the content using Open AI embedding
        """
        # todo: make this Singleton
        client = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-3-small",
            api_key="apoleu",
            azure_endpoint="https://endpoint.openai.azure.com/",
            openai_api_version="2023-07-01-preview",
        )
        text = text.replace("\n", " ")
        return client.embed_documents([text])[0]


@dataclass
class OllamaEmbeddingModel(EmbeddingModel):
    model_name: str
    base_url: str = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")

    def embed(self, text: str) -> List[float]:
        """
        Embeds the content using Open AI embedding
        """
        text = text.replace("\n", " ")
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model_name, "input": [text]},
        )
        return response.json()["embeddings"][0]

