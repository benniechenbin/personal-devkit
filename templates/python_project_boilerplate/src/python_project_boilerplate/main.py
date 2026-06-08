from python_project_boilerplate.core.bootstrap import init_workspace
from python_project_boilerplate.observability.logger import logger


def main() -> None:
    init_workspace()
    logger.info("系统启动成功，进入主循环...")
    # 你的业务代码...


if __name__ == "__main__":
    main()
