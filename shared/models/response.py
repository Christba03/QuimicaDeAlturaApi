from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Any = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str | None = None
    details: Any = None
