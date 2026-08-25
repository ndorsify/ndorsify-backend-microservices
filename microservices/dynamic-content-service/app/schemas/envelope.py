"""Generic response envelope — port of the Java ``NDorsifyUtil<T>``."""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class NDorsifyUtil(BaseModel, Generic[T]):
    status: Optional[str] = None
    message: Optional[str] = None
    data: Optional[T] = None
