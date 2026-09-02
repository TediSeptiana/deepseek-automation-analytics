from pathlib import Path
from docgen.analyzer.python import PythonASTAnalyzer
from docgen.context.builder import DefaultContextBuilder

def test_context_contains_python_identifiers(tmp_path: Path):
    source = tmp_path / "sample.py"
    source.write_text(
        "def triangle_area(base: float, height: float) -> float:\n"
        "    return base * height / 2\n",
        encoding="utf-8",
    )

    module = PythonASTAnalyzer().analyze(source)
    context = DefaultContextBuilder().build(module)

    assert "triangle_area" in context
    assert "base" in context
    assert "height" in context
    assert "float" in context
