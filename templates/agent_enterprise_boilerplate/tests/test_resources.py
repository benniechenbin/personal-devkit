from app.resources import load_prompt


def test_packaged_prompt_can_be_loaded() -> None:
    prompt = load_prompt("planner")

    assert "Planner Prompt" in prompt
