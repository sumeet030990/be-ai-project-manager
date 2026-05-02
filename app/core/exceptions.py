from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str | None = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or f"ERR_{status_code}"


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found.",
            error_code="NOT_FOUND",
        )


class ConflictException(AppException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
        )


class BadRequestException(AppException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST",
        )


class ServiceUnavailableException(AppException):
    def __init__(self, detail: str = "AI provider is not configured."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE",
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )
