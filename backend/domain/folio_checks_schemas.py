from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class MarkFaults(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    volume: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    first: int
    last: int
    feed: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    gutter: FiniteFloat
    faults: list | dict
