from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.settings import BASE_DIR, Settings, get_settings
from app.core.banner import show_banner
from app.observability.logger import logger, setup_logger, shutdown_logger


@dataclass(frozen=True, slots=True)
class BootstrapState:
    settings: Settings
    log_dir: Path


_state: BootstrapState | None = None


def init_workspace(
    app_settings: Settings | None = None,
    *,
    show_startup_banner: bool = True,
) -> BootstrapState:
    """
    初始化项目运行环境。

    适合：
    - 小项目直接调用
    - 中大型项目被 lifecycle 调用
    """
    global _state

    if _state is not None:
        if app_settings is not None and app_settings != _state.settings:
            raise RuntimeError("workspace 已初始化，不能使用不同 settings 重复初始化")
        return _state

    settings = app_settings or get_settings()

    if show_startup_banner:
        show_banner(text=settings.app_name, font="slant")

    log_dir = setup_logger(log_dir=settings.resolved_log_dir)

    _validate_env_vars(settings)
    _ensure_directories(settings)

    logger.info(
        "🚀 工作空间初始化完成：应用={}，环境={}，项目目录={}，日志目录={}",
        settings.app_name,
        settings.app_env,
        BASE_DIR.resolve(),
        log_dir.resolve(),
    )

    _state = BootstrapState(settings=settings, log_dir=log_dir)
    return _state


def shutdown_workspace() -> None:
    """
    关闭 bootstrap 层资源。
    目前主要是 logger。
    """
    global _state

    if _state is None:
        return

    logger.info("🛑 工作空间关闭：{}", _state.settings.app_name)
    shutdown_logger()
    _state = None


def _validate_env_vars(settings: Settings) -> None:
    """
    只检查不配置就必崩的关键环境变量。
    小项目可以先 pass。
    """
    pass


def _ensure_directories(settings: Settings) -> None:
    required_dirs: list[Path] = [
        settings.resolved_log_dir,
        # BASE_DIR / "data",
        # BASE_DIR / "data" / "input",
        # BASE_DIR / "data" / "output",
    ]

    for path in required_dirs:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug("已确保目录存在：{}", path)
