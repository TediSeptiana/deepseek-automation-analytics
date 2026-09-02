from __future__ import annotations
import ast
from pathlib import Path
from docgen.domain.models import (
    ClassInfo, FunctionInfo, ImportInfo, ModuleInfo, ParameterInfo
)

class PythonASTAnalyzer:
    """Analyze Python source using the standard-library AST."""

    def analyze(self, path: Path) -> ModuleInfo:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        functions, classes, imports = [], [], []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._function(node))
            elif isinstance(node, ast.ClassDef):
                classes.append(self._class(node))
            elif isinstance(node, ast.Import):
                imports.append(self._import(node))
            elif isinstance(node, ast.ImportFrom):
                imports.append(self._from_import(node))

        return ModuleInfo(
            name=path.stem,
            path=path,
            docstring=ast.get_docstring(tree),
            functions=tuple(functions),
            classes=tuple(classes),
            imports=tuple(imports),
        )

    def _function(self, node):
        args = node.args
        positional = [*args.posonlyargs, *args.args]
        defaults = [None] * (len(positional) - len(args.defaults))
        defaults.extend(args.defaults)
        params = []

        for arg, default in zip(positional, defaults, strict=True):
            params.append(ParameterInfo(
                name=arg.arg,
                annotation=self._annotation(arg.annotation),
                default=self._expr(default) if default else None,
                kind="positional",
            ))

        if args.vararg:
            params.append(ParameterInfo(
                name=args.vararg.arg,
                annotation=self._annotation(args.vararg.annotation),
                default=None,
                kind="var_positional",
            ))

        for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
            params.append(ParameterInfo(
                name=arg.arg,
                annotation=self._annotation(arg.annotation),
                default=self._expr(default) if default else None,
                kind="keyword_only",
            ))

        if args.kwarg:
            params.append(ParameterInfo(
                name=args.kwarg.arg,
                annotation=self._annotation(args.kwarg.annotation),
                default=None,
                kind="var_keyword",
            ))

        return FunctionInfo(
            name=node.name,
            signature=self._signature(node),
            docstring=ast.get_docstring(node),
            parameters=tuple(params),
            return_annotation=self._annotation(node.returns),
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=tuple(self._expr(d) for d in node.decorator_list),
        )

    def _class(self, node):
        return ClassInfo(
            name=node.name,
            docstring=ast.get_docstring(node),
            bases=tuple(self._expr(b) for b in node.bases),
            methods=tuple(
                self._function(n) for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ),
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            decorators=tuple(self._expr(d) for d in node.decorator_list),
        )

    def _import(self, node):
        return ImportInfo(
            module="",
            names=tuple(a.name for a in node.names),
            alias=next((a.asname for a in node.names if a.asname), None),
            is_from_import=False,
        )

    def _from_import(self, node):
        return ImportInfo(
            module="." * node.level + (node.module or ""),
            names=tuple(a.name for a in node.names),
            alias=None,
            is_from_import=True,
        )

    def _signature(self, node):
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        args = node.args
        positional = [*args.posonlyargs, *args.args]
        defaults = [None] * (len(positional) - len(args.defaults))
        defaults.extend(args.defaults)
        parts = []

        for arg, default in zip(positional, defaults, strict=True):
            value = arg.arg
            if arg.annotation:
                value += f": {self._expr(arg.annotation)}"
            if default:
                value += f" = {self._expr(default)}"
            parts.append(value)

        if args.vararg:
            value = "*" + args.vararg.arg
            if args.vararg.annotation:
                value += f": {self._expr(args.vararg.annotation)}"
            parts.append(value)

        if args.kwonlyargs:
            if not args.vararg:
                parts.append("*")
            for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
                value = arg.arg
                if arg.annotation:
                    value += f": {self._expr(arg.annotation)}"
                if default:
                    value += f" = {self._expr(default)}"
                parts.append(value)

        if args.kwarg:
            value = "**" + args.kwarg.arg
            if args.kwarg.annotation:
                value += f": {self._expr(args.kwarg.annotation)}"
            parts.append(value)

        result = f"{prefix} {node.name}({', '.join(parts)})"
        if node.returns:
            result += f" -> {self._expr(node.returns)}"
        return result

    @staticmethod
    def _annotation(node):
        return PythonASTAnalyzer._expr(node) if node else None

    @staticmethod
    def _expr(node):
        if node is None:
            return ""
        try:
            return ast.unparse(node)
        except Exception:
            return "<unavailable>"
