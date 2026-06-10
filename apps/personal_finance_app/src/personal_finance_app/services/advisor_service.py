from loguru import logger
from openai import OpenAI

from personal_finance_app.config import settings


class AdvisorService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = settings.llm_url
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

    def get_advice(
        self,
        summary_text: str,
        categories: list[dict] | None = None,
    ) -> str:
        """调用大语言模型（LLM）获取财务优化建议。"""
        if not self.client:
            logger.warning("OPENAI_API_KEY is not set. Skipping LLM insights.")
            return "AI advice is unavailable (API key not set)."

        logger.info("Requesting optimization suggestions from LLM...")
        try:
            category_text = self._format_categories(categories)
            prompt = f"""
你是一位谨慎、客观的个人财务分析助理。

以下数据来自程序的确定性计算结果。请只基于这些事实提出建议：
- 不要重新计算金额。
- 不要虚构没有出现的分类。
- 不要给投资、税务、法律建议。
- 建议仅用于个人月度复盘。

【核心指标】
{summary_text}

【分类支出明细】
{category_text}

【输出要求】
请输出 3 条具体、可执行的优化建议。
每条建议需要包含：
1. 观察到的事实
2. 可能的问题
3. 下个月可以执行的具体行动

避免使用“减少不必要开支”这类空泛表达。
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

    def _format_categories(self, categories: list[dict] | None) -> str:
        """将分类数据格式化为紧凑文本。"""
        if not categories:
            return "暂无分类支出明细。"

        lines = []
        for item in categories:
            category = item.get("category", "未分类")
            amount = item.get("amount", 0)
            direction = item.get("direction", "expense")
            lines.append(f"- {category} ({direction}): {amount} 元")
        return "\n".join(lines)
