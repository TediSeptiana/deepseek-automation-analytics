from __future__ import annotations
from pathlib import Path
from typing import Protocol
from .models import ModuleInfo

class PythonAnalyzer(Protocol):
    def analyze(self, path: Path) -> ModuleInfo: ...

class ContextBuilder(Protocol):
    def build(self, module: ModuleInfo) -> str: ...

class PromptBuilder(Protocol):
    def build(self, context: str) -> str: ...

class LLMClient(Protocol):
    async def health(self) -> bool: ...
    async def generate(self, prompt: str) -> str: ...

class DocumentationRenderer(Protocol):
    def render(self, content: str) -> str: ...
