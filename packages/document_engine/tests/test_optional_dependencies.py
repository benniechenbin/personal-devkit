import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "document_engine"


def _top_level_import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])

    return modules


def test_formula_dependency_is_loaded_lazily() -> None:
    imports = _top_level_import_modules(SOURCE_ROOT / "components" / "math_extractor.py")

    assert "pix2text" not in imports


def test_vision_dependency_is_loaded_lazily() -> None:
    imports = _top_level_import_modules(SOURCE_ROOT / "pipelines" / "vision_pdf_pipeline.py")

    assert "paddleocr" not in imports
