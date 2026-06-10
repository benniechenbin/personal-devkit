from loguru import logger
from openai import OpenAI

from personal_finance_app.config import settings


class AdvisorService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = settings.llm_url
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

    def get_advice(self, summary_text: str) -> str:
        """调用大语言模型（LLM）获取财务优化建议。"""
        if not self.client:
            logger.warning("OPENAI_API_KEY is not set. Skipping LLM insights.")
            return "AI advice is unavailable (API key not set)."

        logger.info("Requesting optimization suggestions from LLM...")
        try:
            prompt = f"""
            你是一位专业的个人理财助理。请基于以下用户近期的财务数据事实简报，
            给出3条具体、可执行的财务优化建议。如果发现异常开销，请重点关注。

            {summary_text}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的理财规划师。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            insights = response.choices[0].message.content
            return insights
        except Exception as e:
            logger.error(f"Failed to get LLM insights: {e}")
            return f"Error getting AI advice: {e}"
