from pathlib import Path

from python_project_boilerplate.config.settings import BASE_DIR, settings
from python_project_boilerplate.core.banner import show_banner
from python_project_boilerplate.observability.logger import logger, setup_logger


def _ensure_directories() -> None:
    """防御 2：动态创建必要的物理目录（除日志外的业务目录）"""
    required_dirs: list[Path] = [
        # BASE_DIR / "data" / "input",
        # BASE_DIR / "data" / "output",
    ]
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug("已确保工作目录存在: {}", d.relative_to(BASE_DIR))


def _validate_env_vars() -> None:
    """防御 3：核心配置自检 (Fail-Fast)"""
    # 在具体业务模板中添加那些“如果没配，往下跑一定会崩”的致命配置检查。
    pass


def init_workspace() -> None:
    """初始化项目通用服务与环境安检。"""
    show_banner(text=settings.app_name, font="slant")

    # 0. 【第一优先级】点亮日志雷达，让后续的自检报错有迹可循
    log_dir = setup_logger(log_dir=settings.resolved_log_dir)

    # 1. 运行系统级前置安检
    _validate_env_vars()

    # 2. 挂载物理工作目录
    _ensure_directories()

    # 3. 绿灯放行
    logger.info(
        "🚀 工作空间初始化完成：应用={}，环境={}，项目目录={}，日志目录={}",
        settings.app_name,
        settings.app_env,
        BASE_DIR.resolve(),
        log_dir.resolve(),
    )


def main() -> None:
    init_workspace()

    # 👇 从这里开始编写你的业务逻辑代码
    # logger.info("正在执行主任务...")


if __name__ == "__main__":
    main()
