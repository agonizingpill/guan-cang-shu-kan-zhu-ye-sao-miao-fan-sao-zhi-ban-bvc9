from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class EstimateCount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check_ref: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class BookSlot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    token: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    bench: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    day: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    begin_at: int
    finish_at: int
