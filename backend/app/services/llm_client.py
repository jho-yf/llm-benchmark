import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        provider: str,
        api_base: str,
        api_key: str | None,
        auth_type: str,
        model_id: str,
        params: dict | None = None,
    ):
        self.model_id = model_id
        self.default_params = params or {}

        if auth_type == "bearer":
            self.client = OpenAI(
                api_key="not-needed",
                base_url=api_base,
                default_headers={"Authorization": f"Bearer {api_key}"},
            )
        elif auth_type == "api_key":
            self.client = OpenAI(api_key=api_key, base_url=api_base)
        else:
            self.client = OpenAI(api_key="not-needed", base_url=api_base)

    def generate(self, prompt: str, **kwargs) -> str:
        params = {**self.default_params, **kwargs}
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            **params,
        )
        return response.choices[0].message.content

    def test_connection(self) -> bool:
        try:
            self.generate("Hello", max_tokens=5)
            return True
        except Exception as e:
            logger.warning("Connection test failed: %s", e)
            return False
