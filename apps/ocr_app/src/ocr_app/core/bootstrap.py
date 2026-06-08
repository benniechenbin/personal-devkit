from ocr_app.config.settings import BASE_DIR, Settings, get_settings
from ocr_app.observability.logger import logger, setup_logger


def init_workspace(app_settings: Settings | None = None) -> Settings:
    settings = app_settings or get_settings()
    log_dir = setup_logger(
        log_dir=settings.resolved_log_dir,
        log_level=settings.log_level,
    )
    settings.resolved_output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "工作空间初始化完成：应用={}，环境={}，项目目录={}，日志目录={}，输出目录={}",
        settings.app_name,
        settings.app_env,
        BASE_DIR.resolve(),
        log_dir.resolve(),
        settings.resolved_output_dir.resolve(),
    )
    return settings
