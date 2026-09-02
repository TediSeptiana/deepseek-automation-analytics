from pathlib import Path
from docgen.analyzer.python import PythonASTAnalyzer

def test_analyzer_extracts_functions_and_classes(tmp_path: Path):
    source = tmp_path / "sample.py"
    source.write_text(
        Module docs.