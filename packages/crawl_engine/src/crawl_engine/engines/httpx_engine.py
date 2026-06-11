import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from crawl_engine.schema import ScrapeRequest, ScrapeResponse

logger = logging.getLogger(__name__)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class HttpxEngine:
    """轻量级并发爬虫引擎，极速抓取静态页面"""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(
            verify=False,
            timeout=10.0,
            limits=httpx.Limits(max_connections=50),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"🔄 轻量引擎重试抓取，第 {retry_state.attempt_number} 次..."
        ),
    )
    async def _execute_scrape(self, request: ScrapeRequest) -> ScrapeResponse:
        logger.info(f"⚡ 轻量引擎出击: {request.url}")

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if request.headers:
            headers.update(request.headers)

        response = await self.client.get(request.url, headers=headers)

        # 如果 HTTP 状态码不是 200 系列，直接抛出异常触发 @retry
        response.raise_for_status()

        raw_html = response.text

        # 封装标准返回格式
        return ScrapeResponse(
            success=True,
            url=request.url,
            final_url=str(response.url),
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            raw_html=raw_html,
            content=raw_html,
            content_length=len(raw_html),
        )

    async def fetch_content(self, request: ScrapeRequest) -> ScrapeResponse:
        """安全包裹层，防止崩溃"""
        try:
            return await self._execute_scrape(request)
        except httpx.HTTPStatusError as e:
            logger.exception(f"❌ HTTP 状态错误 {request.url}: {e.response.status_code}")
            return ScrapeResponse(
                success=False,
                url=request.url,
                final_url=str(e.response.url),
                status_code=e.response.status_code,
                content_type=e.response.headers.get("content-type"),
                error_message=f"HTTP {e.response.status_code}",
            )
        except httpx.TimeoutException:
            logger.exception(f"⌛ 请求超时: {request.url}")
            return ScrapeResponse(success=False, url=request.url, error_message="Timeout")
        except Exception as e:
            logger.exception(f"💥 引擎严重崩溃: {request.url}")
            return ScrapeResponse(success=False, url=request.url, error_message=str(e))

    async def close(self) -> None:
        """释放连接池资源"""
        await self.client.aclose()
