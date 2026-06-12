class ProviderEngineError(Exception):
    """Base error for provider-engine."""


class ProviderConfigurationError(ProviderEngineError):
    """Raised when a provider is not configured correctly."""


class ProviderCallError(ProviderEngineError):
    """Raised when a provider call fails after local handling."""


class ProviderParseError(ProviderEngineError):
    """Raised when provider output cannot be parsed into the expected shape."""


class ProviderRouteError(ProviderEngineError):
    """Raised when a provider route is missing or invalid."""
