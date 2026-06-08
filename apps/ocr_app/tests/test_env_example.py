import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_env_example.py"
spec = importlib.util.spec_from_file_location("ocr_app_generate_env_example", SCRIPT_PATH)
assert spec is not None
generate_env_example = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(generate_env_example)


def test_build_env_example_hides_secrets() -> None:
    content = generate_env_example.build_env_example()

    assert "APP_NAME=ocr-app" in content
    assert "DOC_PROCESSING_MODE=vision" in content
    assert "OPENAI_API_KEY=\n" in content
