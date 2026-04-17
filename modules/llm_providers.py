from __future__ import annotations

from abc import ABC, abstractmethod

from anthropic import Anthropic
from google import genai
from openai import OpenAI


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider")
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return (response.text or "").strip()


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIProvider")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        message = response.choices[0].message.content if response.choices else ""
        return (message or "").strip()


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, max_tokens: int = 2000):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicProvider")
        self.model = model
        self.max_tokens = max_tokens
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.content:
            return ""
        content_part = response.content[0]
        return getattr(content_part, "text", "").strip()
