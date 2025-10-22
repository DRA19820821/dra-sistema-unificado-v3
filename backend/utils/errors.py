class AppError(Exception):
    """Erro base da aplicação."""
    def __init__(self, message: str, code: str = "APP_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class APIError(AppError):
    def __init__(self, message: str, provider: str, status_code: int, details: dict = None):
        super().__init__(message, "API_ERROR", details)
        self.provider = provider
        self.status_code = status_code

class RateLimitError(AppError):
    def __init__(self, provider: str, details: dict = None):
        super().__init__(f"Rate limit atingido para {provider}", "RATE_LIMIT_ERROR", details)

class TimeoutError(AppError):
    def __init__(self, operation: str, details: dict = None):
        super().__init__(f"Timeout na operação: {operation}", "TIMEOUT_ERROR", details)

def is_recoverable_error(error: Exception) -> bool:
    """Determina se erro é recuperável."""
    return isinstance(error, (TimeoutError, APIError))

def should_abort(error: Exception) -> bool:
    """Determina se deve abortar processamento."""
    return isinstance(error, RateLimitError)