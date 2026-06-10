from unittest.mock import MagicMock, patch

from personal_finance_app.services.advisor_service import AdvisorService


def test_format_categories_empty():
    service = AdvisorService()
    assert service._format_categories(None) == "暂无分类支出明细。"
    assert service._format_categories([]) == "暂无分类支出明细。"


def test_format_categories_with_data():
    service = AdvisorService()
    categories = [
        {"category": "餐饮", "amount": 1050.0, "direction": "expense"},
        {"category": "交通", "amount": 300.0, "direction": "expense"},
    ]
    formatted = service._format_categories(categories)
    assert "- 餐饮 (expense): 1050.0 元" in formatted
    assert "- 交通 (expense): 300.0 元" in formatted


@patch("personal_finance_app.services.advisor_service.OpenAI")
@patch("personal_finance_app.services.advisor_service.settings")
def test_get_advice_no_api_key(mock_settings, mock_openai):
    mock_settings.openai_api_key = None
    service = AdvisorService()
    advice = service.get_advice("Summary text")
    assert "AI advice is unavailable" in advice


@patch("personal_finance_app.services.advisor_service.OpenAI")
@patch("personal_finance_app.services.advisor_service.settings")
def test_get_advice_with_client_success(mock_settings, mock_openai):
    mock_settings.openai_api_key = "test-key"
    mock_settings.openai_model = "test-model"
    mock_settings.llm_url = "test-url"

    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Test advice"

    service = AdvisorService()
    advice = service.get_advice("Summary text", categories=[{"category": "Food", "amount": 100}])

    assert advice == "Test advice"
    mock_client.chat.completions.create.assert_called_once()
    # Check if prompt contains categories
    args, kwargs = mock_client.chat.completions.create.call_args
    prompt = kwargs["messages"][1]["content"]
    assert "Food (expense): 100 元" in prompt
    assert "Summary text" in prompt
