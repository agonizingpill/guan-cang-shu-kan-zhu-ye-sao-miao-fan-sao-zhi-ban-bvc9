from typing import Annotated, Optional

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
    # Optional active audit shift. When supplied, the late check immediately
    # replans that shift's unclaimed pages.
    shift: Optional[str] = None
    shift_code: Optional[str] = None
    audit_shift: Optional[str] = None
    batch: Optional[str] = None
    quota: Optional[int] = None
    limit: Optional[int] = None
