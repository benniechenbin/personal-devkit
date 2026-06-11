from __future__ import annotations

from subtitle_harvester_app.config.settings import Settings, get_settings
from subtitle_harvester_app.observability.logger import logger, setup_logger


def init_workspace(
    app_settings: Settings | None = None,
    *,
    require_tmdb: bool = False,
) -> Settings:
    settings = app_settings or get_settings()

    setup_logger(
        log_dir=settings.resolved_log_dir,
        log_level=settings.log_level,
    )
    settings.resolved_output_dir.mkdir(parents=True, exist_ok=True)

    if require_tmdb and not settings.tmdb_api_key:
        raise RuntimeError(
            "缺少 TMDB_API_KEY，请在 .env 中配置 TMDb v3 API Key 或 Read Access Token。"
        )

    logger.info(
        "工作空间初始化完成：应用={}，环境={}，输出目录={}",
        settings.app_name,
        settings.app_env,
        settings.resolved_output_dir,
    )
    return settings
