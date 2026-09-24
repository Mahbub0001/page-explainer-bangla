import logging
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(
        self,
        code: str,
        http_status: int,
        message: str,
        message_bn: str,
        headers: Optional[dict] = None
    ):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message
        self.message_bn = message_bn
        self.headers = headers or {}


# Pre-defined error factories / common errors
def err_page_not_found(msg="Page index not found") -> AppError:
    return AppError(
        code="PAGE_NOT_FOUND",
        http_status=404,
        message=msg,
        message_bn="পেজ পাওয়া যায়নি, আবার বিশ্লেষণ করুন।"
    )

def err_text_too_short(msg="Page text too short") -> AppError:
    return AppError(
        code="TEXT_TOO_SHORT",
        http_status=422,
        message=msg,
        message_bn="এই পেজে বিশ্লেষণ করার মতো যথেষ্ট লেখা নেই।"
    )

def err_payload_too_large(msg="Payload exceeds maximum allowed size") -> AppError:
    return AppError(
        code="PAYLOAD_TOO_LARGE",
        http_status=413,
        message=msg,
        message_bn="পেজ বা লেখা অনেক বেশি বড়।"
    )

def err_validation(msg="Validation error") -> AppError:
    return AppError(
        code="VALIDATION_ERROR",
        http_status=422,
        message=msg,
        message_bn="অনুরোধের তথ্য সঠিক নয়।"
    )

def err_rate_limited(retry_after: int = 60) -> AppError:
    return AppError(
        code="RATE_LIMITED",
        http_status=429,
        message="Too many requests",
        message_bn="অনেক বেশি অনুরোধ এসেছে। কিছুক্ষণ পরে আবার চেষ্টা করুন।",
        headers={"Retry-After": str(retry_after)}
    )

def err_llm_quota_exceeded(msg="AI usage quota exceeded") -> AppError:
    return AppError(
        code="LLM_QUOTA_EXCEEDED",
        http_status=429,
        message=msg,
        message_bn="AI-এর ব্যবহারের সীমা শেষ। কিছুক্ষণ পরে আবার চেষ্টা করুন।"
    )

def err_invalid_api_key(msg="Missing or invalid Gemini API key") -> AppError:
    return AppError(
        code="INVALID_API_KEY",
        http_status=500,
        message=msg,
        message_bn="Gemini API Key সেট করা হয়নি বা সঠিক নয়।"
    )

def err_llm_unavailable(msg="LLM service temporarily unavailable") -> AppError:
    return AppError(
        code="LLM_UNAVAILABLE",
        http_status=502,
        message=msg,
        message_bn="AI সার্ভারে সাময়িক সমস্যা হয়েছে। কিছুক্ষণ পরে আবার চেষ্টা করুন।"
    )

def err_embedding_failed(msg="Failed to generate embeddings") -> AppError:
    return AppError(
        code="EMBEDDING_FAILED",
        http_status=502,
        message=msg,
        message_bn="পেজের লেখার এমবেডিং তৈরি করতে সমস্যা হয়েছে।"
    )

def err_internal(msg="Internal server error") -> AppError:
    return AppError(
        code="INTERNAL_ERROR",
        http_status=500,
        message=msg,
        message_bn="কিছু একটা সমস্যা হয়েছে। আবার চেষ্টা করুন।"
    )


def map_llm_exception(exc: Exception) -> AppError:
    """Map LLM/GenAI exceptions to standard AppError."""
    if isinstance(exc, AppError):
        return exc

    err_str = str(exc).lower()
    exc_type = type(exc).__name__.lower()

    if "resourceexhausted" in exc_type or "resource_exhausted" in err_str or "429" in err_str or "quota" in err_str:
        return err_llm_quota_exceeded(str(exc))

    if "invalid_api_key" in err_str or "api key" in err_str or "permissiondenied" in exc_type or "unauthenticated" in err_str:
        return err_invalid_api_key(str(exc))

    if "timeout" in err_str or "deadlineexceeded" in exc_type or "timed out" in err_str:
        return err_llm_unavailable(f"Request timed out: {exc}")

    if "embedding" in err_str:
        return err_embedding_failed(str(exc))

    return err_llm_unavailable(str(exc))


def format_error_response(app_error: AppError) -> JSONResponse:
    content = {
        "error": {
            "code": app_error.code,
            "message": app_error.message,
            "message_bn": app_error.message_bn,
        }
    }
    return JSONResponse(
        status_code=app_error.http_status,
        content=content,
        headers=app_error.headers
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return format_error_response(exc)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Summarize validation error messages
    details = exc.errors()
    msg = "Validation failed: " + "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in details)
    return format_error_response(err_validation(msg))


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return format_error_response(err_page_not_found(exc.detail))
    return format_error_response(AppError(
        code="INTERNAL_ERROR" if exc.status_code >= 500 else "VALIDATION_ERROR",
        http_status=exc.status_code,
        message=str(exc.detail),
        message_bn="কিছু একটা সমস্যা হয়েছে। আবার চেষ্টা করুন।"
    ))


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception: %s", exc)
    return format_error_response(err_internal(str(exc)))
