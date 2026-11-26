from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class AcceptPages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    slot: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    mapped_pages: list | dict
