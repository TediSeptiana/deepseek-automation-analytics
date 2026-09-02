from __future__ import annotations
from docgen.domain.models import ClassInfo, FunctionInfo, ModuleInfo

class DefaultContextBuilder:
    """Convert deterministic AST information into LLM-readable context."""

    def build(self, module: ModuleInfo) -> str:
        sections = [f"MODULE: {module.name}", f"SOURCE: {module.path}"]

        if module.docstring:
            sections.append(f"MODULE DOCSTRING:\n{module.docstring}")

        if module.imports:
            lines = []
            for item in module.imports:
                prefix = f"from {item.module} import" if item.is_from_import else "import"
                lines.append(f"- {prefix} {', '.join(item.names)}")
            sections.append("IMPORTS:\n" + "\n".join(lines))

        if module.functions:
            sections.append(
                "MODULE FUNCTIONS:\n" +
                "\n\n".join(self._function(f) for f in module.functions)
            )

        if module.classes:
            sections.append(
                "CLASSES:\n" +
                "\n\n".join(self._class(c) for c in module.classes)
            )

        return "\n\n".join(sections)

    def _function(self, f: FunctionInfo) -> str:
        params = "\n".join(
            f"  - {p.name}: annotation={p.annotation!r}, "
            f"default={p.default!r}, kind={p.kind}"
            for p in f.parameters
        ) or "  - none"
        return (
            f"FUNCTION: {f.name}\n"
            f"signature: {f.signature}\n"
            f"async: {f.is_async}\n"
            f"lines: {f.line_start}-{f.line_end}\n"
            f"decorators: {', '.join(f.decorators) or 'none'}\n"
            f"return: {f.return_annotation or 'none'}\n"
            f"existing_docstring: {f.docstring or 'none'}\n"
            f"parameters:\n{params}"
        )

    def _class(self, c: ClassInfo) -> str:
        methods = "\n\n".join(self._function(m) for m in c.methods) or "none"
        return (
            f"CLASS: {c.name}\n"
            f"bases: {', '.join(c.bases) or 'none'}\n"
            f"lines: {c.line_start}-{c.line_end}\n"
            f"decorators: {', '.join(c.decorators) or 'none'}\n"
            f"existing_docstring: {c.docstring or 'none'}\n"
            f"METHODS:\n{methods}"
        )
