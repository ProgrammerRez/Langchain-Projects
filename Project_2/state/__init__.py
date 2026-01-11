from pydantic import BaseModel, Field
from typing import List, Literal, Any, Optional,Tuple
from datetime import datetime


Verdict = Literal["A", "R", "E"]  # Answer, Request Info, Escalate


class SupportTicketState(BaseModel):
    # -------------------------
    # Identity
    # -------------------------
    ticket_id: str

    # -------------------------
    # User input
    # -------------------------
    ticket_text: str = Field(description="Latest user message")
    messages: List[Tuple[str,str]] = Field(default_factory=list)

    # -------------------------
    # Extracted information
    # -------------------------
    info_list: List[str] = Field(
        default_factory=list,
        description="All confirmed facts provided by the user"
    )

    # -------------------------
    # Knowledge & retrieval
    # -------------------------
    retrieved_from_kb: List[Any] = Field(
        default_factory=list,
        description="KB + past ticket retrieval results"
    )

    # -------------------------
    # Decision intelligence
    # -------------------------
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in ability to auto-resolve"
    )

    current_verdict: Optional[Verdict] = None
    final_verdict: Optional[Verdict] = None

    number_of_request_infos: int = 0

    # -------------------------
    # SLA & timing (NON-NEGOTIABLE)
    # -------------------------
    ticket_created_at: datetime
    last_agent_action_at: Optional[datetime] = None
    last_user_message_at: Optional[datetime] = None

    sla_seconds: int = Field(description="Maximum allowed response time")

    # -------------------------
    # Output (only valid if ANSWER)
    # -------------------------
    answer: Optional[str] = None
