from __future__ import annotations
import argparse
import asyncio
from pathlib import Path

from docgen.analyzer.python import PythonASTAnalyzer
from docgen.application import DocumentationGenerator
from docgen.context.builder import DefaultContextBuilder
from docgen.llm.local import LocalLLMClient
from docgen.prompting.documentation import DefaultDocumentationPromptBuilder
from docgen.renderer.markdown import MarkdownRenderer

def parse_args():
    parser = argparse.ArgumentParser(
        prog="docgen",
        description="Generate Python documentation using a local LLM."
    )
    parser.add_argument("source", type=Path, help="Python file or directory.")
    parser.add_argument("--output", type=Path, default=Path("./docs"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-delay", type=float, default=2.0)
    parser.add_argument("--include-private", action="store_true")
    return parser.parse_args()

def collect_sources(source: Path, include_private: bool):
    source = source.resolve()

    if source.is_file():
        if source.suffix != ".py":
            raise ValueError("Source file must have a .py extension.")
        return [source], source.parent

    if not source.is_dir():
        raise FileNotFoundError(f"Source does not exist: {source}")

    files = sorted(source.rglob("*.py"))

    excluded_dirs = {
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".git",
        "docs",
        "docgen_v1",
    }

    files = [
        p for p in files
        if not any(
            part in excluded_dirs
            for part in p.relative_to(source).parts
        )
    ]

    if not include_private:
        files = [
            p for p in files
            if not any(
                part.startswith("_")
                for part in p.relative_to(source).parts
            )
        ]
    if not files:
        raise ValueError(f"No Python files found under: {source}")

    return files, source

async def run(args) -> int:
    sources, source_root = collect_sources(args.source, args.include_private)
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    llm = LocalLLMClient(
        args.base_url, timeout=args.timeout,
        retries=args.retries, retry_delay=args.retry_delay
    )

    generator = DocumentationGenerator(
        analyzer=PythonASTAnalyzer(),
        context_builder=DefaultContextBuilder(),
        prompt_builder=DefaultDocumentationPromptBuilder(),
        llm=llm,
        renderer=MarkdownRenderer(),
    )

    async with llm:
        print(f"[INFO] Source files : {len(sources)}")
        print(f"[INFO] Output       : {output_dir}")
        print(f"[INFO] LLM endpoint : {args.base_url}")
        print("[INFO] Checking LLM readiness...")

        if not await llm.health():
            print("[ERROR] Local LLM is not ready.")
            print("[ERROR] Expected GET /health to return service_status='ready'.")
            return 2

        print("[OK] Local LLM is ready.")
        stats = await generator.generate_many(sources, output_dir, source_root)

    print("\nGeneration summary")
    print("-------------------")
    print(f"Processed : {stats.processed}")
    print(f"Succeeded : {stats.succeeded}")
    print(f"Failed    : {stats.failed}")
    return 0 if stats.failed == 0 else 1

def main() -> None:
    args = parse_args()
    try:
        raise SystemExit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        print("\n[INFO] Cancelled.")
        raise SystemExit(130)

if __name__ == "__main__":
    main()
