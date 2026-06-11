from __future__ import annotations

import re
from typing import Any


def render_prompt(template: str, **variables: Any) -> str:
    """渲染 prompt 模板。

    如果安装了 Jinja2，就使用 Jinja2；否则退回到简单的 ``{{ variable }}``
    替换，以保持 SDK 的依赖面尽量小。
    """
    try:
        from jinja2 import Template
    except ModuleNotFoundError:
        return _render_with_lightweight_replacement(template, variables)

    return str(Template(template).render(**variables))


def _render_with_lightweight_replacement(
    template: str,
    variables: dict[str, Any],
) -> str:
    pattern = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            return match.group(0)
        value = variables[key]
        if isinstance(value, list | tuple | set):
            return ", ".join(str(item) for item in value)
        return str(value)

    return pattern.sub(replace, template)
