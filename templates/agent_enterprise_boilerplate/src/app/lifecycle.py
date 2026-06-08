from __future__ import annotations

import atexit
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field

from app.config.settings import Settings, get_settings
from app.container.container import Container
from app.core.bootstrap import init_workspace, shutdown_workspace
from app.runtime.runner import AgentRunner
from app.workflows.langgraph_workflow import LangGraphWorkflow


@dataclass(slots=True)
class App:
    settings: Settings
    container: Container
    runner: AgentRunner

    _started: bool = field(default=False, init=False, repr=False)
    _atexit_registered: bool = field(default=False, init=False, repr=False)

    @property
    def started(self) -> bool:
        return self._started

    def start(
        self,
        *,
        show_startup_banner: bool = True,
        register_atexit: bool = True,
    ) -> App:
        if self._started:
            return self

        init_workspace(
            app_settings=self.settings,
            show_startup_banner=show_startup_banner,
        )

        try:
            if hasattr(self.container, "start"):
                self.container.start()

            self._started = True

            if register_atexit and not self._atexit_registered:
                atexit.register(self.shutdown)
                self._atexit_registered = True

            return self

        except Exception:
            shutdown_workspace()
            raise

    def shutdown(self) -> None:
        if not self._started:
            return

        try:
            if hasattr(self.runner, "shutdown"):
                self.runner.shutdown()

            if hasattr(self.container, "shutdown"):
                self.container.shutdown()

        finally:
            shutdown_workspace()
            self._started = False


def create_app(app_settings: Settings | None = None) -> App:
    """
    只创建对象，不启动副作用。
    适合测试和依赖注入。
    """
    settings = app_settings or get_settings()

    container = Container.build(app_settings=settings)
    workflow = LangGraphWorkflow(container=container)
    runner = AgentRunner(workflow=workflow, container=container)

    return App(
        settings=settings,
        container=container,
        runner=runner,
    )


def build_app(
    app_settings: Settings | None = None,
    *,
    auto_start: bool = True,
    show_startup_banner: bool = True,
    register_atexit: bool = True,
) -> App:
    """
    中大型项目推荐入口。
    默认 create + start。
    """
    app = create_app(app_settings=app_settings)

    if auto_start:
        app.start(
            show_startup_banner=show_startup_banner,
            register_atexit=register_atexit,
        )

    return app


@contextmanager
def lifespan(
    app_settings: Settings | None = None,
    *,
    show_startup_banner: bool = True,
) -> Generator[App, None, None]:
    """
    更严谨的上下文入口。
    适合 CLI、批处理、测试环境。
    """
    app = build_app(
        app_settings=app_settings,
        auto_start=True,
        show_startup_banner=show_startup_banner,
        register_atexit=False,
    )

    try:
        yield app
    finally:
        app.shutdown()
