"""crawl_engine 的通用异常定义。"""


class CrawlEngineError(Exception):
    """所有 crawl_engine 异常的基类。"""

    pass


class EngineError(CrawlEngineError):
    """当爬取引擎（httpx, crawl4ai 等）发生底层错误时抛出。"""

    pass


class DownloadError(CrawlEngineError):
    """当文件下载或附件处理失败时抛出。"""

    pass


class ExtractionError(CrawlEngineError):
    """当从页面抽取内容或解压文件失败时抛出。"""

    pass
