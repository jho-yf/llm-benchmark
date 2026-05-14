from unittest.mock import MagicMock, patch

from app.services.llm_client import LLMClient


def test_bearer_auth():
    with patch("app.services.llm_client.OpenAI") as MockOpenAI:
        client = LLMClient(
            provider="custom",
            api_base="http://localhost:8000/v1",
            api_key="my-token",
            auth_type="bearer",
            model_id="test-model",
        )
        MockOpenAI.assert_called_once_with(
            api_key="not-needed",
            base_url="http://localhost:8000/v1",
            default_headers={"Authorization": "Bearer my-token"},
        )


def test_api_key_auth():
    with patch("app.services.llm_client.OpenAI") as MockOpenAI:
        client = LLMClient(
            provider="openai",
            api_base="https://api.openai.com/v1",
            api_key="sk-xxx",
            auth_type="api_key",
            model_id="gpt-4o",
        )
        MockOpenAI.assert_called_once_with(
            api_key="sk-xxx",
            base_url="https://api.openai.com/v1",
        )


def test_no_auth():
    with patch("app.services.llm_client.OpenAI") as MockOpenAI:
        client = LLMClient(
            provider="ollama",
            api_base="http://localhost:11434/v1",
            api_key=None,
            auth_type="none",
            model_id="llama3",
        )
        MockOpenAI.assert_called_once_with(
            api_key="not-needed",
            base_url="http://localhost:11434/v1",
        )


def test_generate():
    with patch("app.services.llm_client.OpenAI") as MockOpenAI:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = "hello"
        MockOpenAI.return_value.chat.completions.create.return_value = mock_resp

        client = LLMClient("openai", "http://x", "k", "api_key", "m")
        result = client.generate("hi")
        assert result == "hello"


def test_test_connection_success():
    with patch("app.services.llm_client.OpenAI") as MockOpenAI:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = "ok"
        MockOpenAI.return_value.chat.completions.create.return_value = mock_resp

        client = LLMClient("openai", "http://x", "k", "api_key", "m")
        assert client.test_connection() is True


def test_test_connection_failure():
    with patch("app.services.llm_client.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception("fail")

        client = LLMClient("openai", "http://x", "k", "api_key", "m")
        assert client.test_connection() is False
