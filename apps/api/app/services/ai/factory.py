from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.mock_provider import MockAIProvider


def get_ai_provider() -> AIProvider:
    if settings.AI_PROVIDER == "deepseek" and settings.ALLOW_EXTERNAL_AI and settings.DEEPSEEK_API_KEY:
        from app.services.ai.deepseek_provider import DeepSeekAIProvider

        return DeepSeekAIProvider(api_key=settings.DEEPSEEK_API_KEY, model=settings.AI_MODEL)
    return MockAIProvider()
