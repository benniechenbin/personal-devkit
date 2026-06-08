from enum import StrEnum


class AppEnv(StrEnum):
    DEV = "development"
    TEST = "testing"
    PROD = "production"


class ModelProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
