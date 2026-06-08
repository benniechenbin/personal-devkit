from importlib.resources import files


def load_prompt(name: str) -> str:
    """按简短名称加载随包发布的提示词。"""
    return files("app.resources").joinpath(f"{name}_prompt.md").read_text(encoding="utf-8")
