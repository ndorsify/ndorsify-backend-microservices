"""Response DTO — port of the Java ``Questions`` DTO."""
from typing import Optional

from pydantic import BaseModel


class Questions(BaseModel):
    question: Optional[str] = None
    dataType: Optional[str] = None
    options: Optional[str] = None
