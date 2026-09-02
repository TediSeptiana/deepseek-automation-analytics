from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class ParameterInfo:
    name: str
    annotation: str | None
    default: str | None
    kind: str

@dataclass(frozen=True)
class FunctionInfo:
    name: str
    signature: str
    docstring: str | None
    parameters: tuple[ParameterInfo, ...]
    return_annotation: str | None
    line_start: int
    line_end: int
    is_async: bool
    decorators: tuple[str, ...] = ()

@dataclass(frozen=True)
class ClassInfo:
    name: str
    docstring: str | None
    bases: tuple[str, ...]
    methods: tuple[FunctionInfo, ...]
    line_start: int
    line_end: int
    decorators: tuple[str, ...] = ()

@dataclass(frozen=True)
class ImportInfo:
    module: str
    names: tuple[str, ...]
    alias: str | None
    is_from_import: bool

@dataclass(frozen=True)
class ModuleInfo:
    name: str
    path: Path
    docstring: str | None
    functions: tuple[FunctionInfo, ...]
    classes: tuple[ClassInfo, ...]
    imports: tuple[ImportInfo, ...]

@dataclass(frozen=True)
class DocumentationResult:
    source: Path
    output: Path
    content: str
    
@dataclass
class GenerationStats:
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
