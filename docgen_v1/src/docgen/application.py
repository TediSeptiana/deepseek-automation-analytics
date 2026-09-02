from __future__ import annotations

import json
from pathlib import Path

from docgen.domain.interfaces import (
    ContextBuilder,
    DocumentationRenderer,
    LLMClient,
    PromptBuilder,
    PythonAnalyzer,
)
from docgen.domain.models import DocumentationResult, GenerationStats


class DocumentationGenerator:
    """Orchestrate the documentation pipeline."""

    def __init__(
        self,
        analyzer: PythonAnalyzer,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        llm: LLMClient,
        renderer: DocumentationRenderer,
    ) -> None:
        self._analyzer = analyzer
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._llm = llm
        self._renderer = renderer

    async def generate_file(
        self,
        source: Path,
        output_dir: Path,
        source_root: Path,
    ) -> DocumentationResult:
        module = self._analyzer.analyze(source)
        context = self._context_builder.build(module)
        prompt = self._prompt_builder.build(context)

        raw = await self._llm.generate(prompt)

        print(f"\n[DEBUG] {source.name}")
        print(f"[DEBUG] Response length: {len(raw)}")
        print(f"[DEBUG] Response ending:")
        print(raw[-500:])

        data = json.loads(raw)

        # Render JSON menjadi Markdown
        content = self._renderer.render(raw)

        relative = source.relative_to(source_root)

        # Folder output
        markdown_dir = output_dir / "dokumentation_md"
        json_dir = output_dir / "dokumentation_json"

        markdown_output = markdown_dir / relative.with_suffix(".md")
        json_output = json_dir / relative.with_suffix(".json")

        # Pastikan directory tersedia
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.parent.mkdir(parents=True, exist_ok=True)

        # Simpan Markdown
        markdown_output.write_text(
            content,
            encoding="utf-8",
        )

        # Simpan JSON
        json_output.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return DocumentationResult(
            source=source,
            output=markdown_output,
            content=content,
        )

    async def generate_many(
        self,
        sources: list[Path],
        output_dir: Path,
        source_root: Path,
    ) -> GenerationStats:
        stats = GenerationStats()

        for source in sources:
            stats.processed += 1

            try:
                result = await self.generate_file(
                    source,
                    output_dir,
                    source_root,
                )

                stats.succeeded += 1

                print(
                    f"[OK] {result.source} -> {result.output}"
                )

            except Exception as exc:
                stats.failed += 1

                message = f"{source}: {exc}"
                stats.errors.append(message)

                print(f"[ERROR] {message}")

        return stats