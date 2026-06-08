import asyncio
import logging

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl_engine.schema import ScrapeRequest, ScrapeResponse
from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class Crawl4AIRequest(ScrapeRequest):
    """Crawl4AI 专用扩展契约"""

    remove_noise: bool = Field(default=True)
    max_length: int = Field(default=10000)
    css_schema: dict | None = Field(default=None)
    wait_for: str | None = Field(default=None)
    js_code: list[str] | None = Field(default=None)


class WebScraper:
    """纯粹的爬虫引擎，没有任何写死的业务逻辑"""

    def __init__(self, headless: bool = True):
        # 【架构级改进】：让实例具备状态，方便外部控制是否弹窗调试
        self.headless = headless

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=lambda retry_state: logger.warning(
            f"正在重试抓取，第 {retry_state.attempt_number} 次..."
        ),
    )
    async def _execute_scrape(self, request: Crawl4AIRequest) -> ScrapeResponse:
        """核心业务逻辑（保留了你全部的出色配置和防死锁设计）"""
        logger.info(f"🕸️ 引擎接收到爬取任务: {request.url}")

        DEFAULT_USER_AGENT = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )  # 动态传入 self.headless
        browser_config = BrowserConfig(
            headless=self.headless,
            verbose=False,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )

        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=10,
            page_timeout=request.timeout_ms,
            wait_for=request.wait_for,
            js_code=request.js_code,
            magic=True,
            flatten_shadow_dom=True,
        )

        # 按需加载过滤器 (你的优秀设计)
        if request.remove_noise:
            run_config.markdown_generator = DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48, threshold_type="fixed", min_word_threshold=0
                )
            )
        if request.css_schema:
            run_config.extraction_strategy = JsonCssExtractionStrategy(request.css_schema)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # 双重超时保护 (你的优秀设计)
            result = await asyncio.wait_for(
                crawler.arun(url=request.url, config=run_config),
                timeout=(request.timeout_ms / 1000) + 10,
            )

            if result.success:
                raw_content = (
                    result.markdown.fit_markdown
                    if request.remove_noise
                    else result.markdown.raw_markdown
                )
                if not raw_content:
                    raw_content = result.markdown.raw_markdown

                # 按请求要求的长度截断
                final_content = raw_content[: request.max_length]

                return ScrapeResponse(
                    success=True,
                    url=request.url,
                    content=final_content,
                    raw_html=result.html,
                    extracted_data=result.extracted_content,
                )
            else:
                return ScrapeResponse(
                    success=False,
                    url=request.url,
                    error_message=f"HTTP {result.status_code}: {result.error_message}",
                )

    async def fetch_content(self, request: Crawl4AIRequest) -> ScrapeResponse:
        """
        公开接口：负责包裹安全网，防止底层崩溃影响整个系统
        """
        try:
            return await self._execute_scrape(request)
        except asyncio.TimeoutError:
            logger.exception(f"抓取严重超时: {request.url}")
            return ScrapeResponse(success=False, url=request.url, error_message="Asyncio Timeout")
        except Exception as e:
            logger.exception(f"爬虫引擎发生崩溃: {request.url}")
            return ScrapeResponse(success=False, url=request.url, error_message=str(e))
