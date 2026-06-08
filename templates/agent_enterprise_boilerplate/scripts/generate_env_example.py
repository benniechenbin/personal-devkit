from __future__ import annotations

import argparse
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, get_args

from app.config.settings import Settings
from pydantic import AliasChoices, SecretBytes, SecretStr
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings

DEFAULT_OUTPUT_FILE = Path(".env.example")
SECRET_FIELD_MARKERS = ("api_key", "secret", "token", "password")


def _annotation_contains_secret(annotation: Any) -> bool:
    if annotation in {SecretStr, SecretBytes}:
        return True
    return any(_annotation_contains_secret(arg) for arg in get_args(annotation))


def _is_secret_field(field_name: str, field: FieldInfo) -> bool:
    return _annotation_contains_secret(field.annotation) or any(
        marker in field_name.lower() for marker in SECRET_FIELD_MARKERS
    )


def _env_name(
    field_name: str,
    field: FieldInfo,
    settings_class: type[BaseSettings],
) -> str:
    alias = field.validation_alias
    if isinstance(alias, str):
        return alias
    if isinstance(alias, AliasChoices):
        first_string_alias = next(
            (choice for choice in alias.choices if isinstance(choice, str)),
            None,
        )
        if first_string_alias:
            return first_string_alias

    env_prefix = str(settings_class.model_config.get("env_prefix", ""))
    return f"{env_prefix}{field_name}".upper()


def _default_to_env_value(field_name: str, field: FieldInfo) -> str:
    if _is_secret_field(field_name, field):
        return ""

    value = field.default
    if value is PydanticUndefined or value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def build_env_example(settings_class: type[BaseSettings] = Settings) -> str:
    lines = [
        "# 由 app.config.settings.Settings 自动生成。",
        "# 请勿在此文件中填写真实密钥。",
        "",
    ]

    for field_name, field in settings_class.model_fields.items():
        if field.description:
            lines.append(f"# {field.description}")
        lines.append(
            f"{_env_name(field_name, field, settings_class)}="
            f"{_default_to_env_value(field_name, field)}"
        )

    return "\n".join(lines) + "\n"


def write_env_example(output_file: Path = DEFAULT_OUTPUT_FILE) -> bool:
    content = build_env_example()
    if output_file.exists() and output_file.read_text(encoding="utf-8") == content:
        return False
    output_file.write_text(content, encoding="utf-8")
    return True


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="根据 app.config.settings.Settings 生成 .env.example。"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    content = build_env_example()

    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        if current == content:
            return 0
        print(f"{args.output} is out of date. Run `make env-example`.", file=sys.stderr)
        return 1

    changed = write_env_example(args.output)
    if changed:
        print(f"Updated {args.output}")
    else:
        print(f"{args.output} is already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
