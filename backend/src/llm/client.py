import os
import json
from typing import Optional
from loguru import logger

GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "").strip()
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip()


class LLMClient:
    def __init__(self):
        self.provider = "stub"
        self._client = None
        if GIGACHAT_API_KEY:
            try:
                from gigachat import GigaChat
                self._client = GigaChat(
                    credentials=GIGACHAT_API_KEY,
                    scope=GIGACHAT_SCOPE,
                    verify_ssl_certs=False,
                    model="GigaChat-2-Pro",
                )
                self.provider = "gigachat"
                logger.info("LLM provider: GigaChat")
            except Exception as e:
                logger.error(f"GigaChat init failed: {e}. Falling back to stub.")
        else:
            logger.warning("GIGACHAT_API_KEY пуст — LLM работает в режиме заглушки.")

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "gigachat" and self._client is not None:
            from gigachat.models import Chat, Messages, MessagesRole
            messages = [
                Messages(role=MessagesRole.SYSTEM, content=system_prompt),
                Messages(role=MessagesRole.USER, content=user_prompt),
            ]
            response = self._client.chat(Chat(messages=messages, temperature=0.2, max_tokens=2000))
            return response.choices[0].message.content
        return json.dumps({
            "is_weak_signal": True,
            "confidence": 0.5,
            "technology": "заглушка",
            "description": "LLM не подключён — это заглушка.",
            "advantage": "",
            "case_example": "",
            "why_weak_signal": "Нет ключа GigaChat.",
            "why_this_score": "",
            "stage": "",
            "trend": "",
            "excluded_trends": [],
        }, ensure_ascii=False)


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client