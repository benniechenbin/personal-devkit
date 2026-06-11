import asyncio

from loguru import logger

from app.core.constants import DEFAULT_RUN_INPUT
from app.lifecycle import build_app
from app.runtime.events import RunStatus


async def main_async() -> int:
    app = build_app()
    result = await app.runner.arun(DEFAULT_RUN_INPUT)
    if result["status"] == RunStatus.FAILED.value:
        logger.error("Agent run failed: {}", result)
        return 1

    logger.info("Agent run completed: {}", result)
    return 0


def main() -> None:
    try:
        exit_code = asyncio.run(main_async())
        if exit_code:
            raise SystemExit(exit_code)
    except KeyboardInterrupt:
        logger.info("应用已被中断。")
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
