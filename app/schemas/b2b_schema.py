from pydantic import BaseModel, Field


class WeightSimulationRequest(BaseModel):
    price: float = Field(default=35, ge=0, le=100)
    delivery: float = Field(default=20, ge=0, le=100)
    compliance: float = Field(default=25, ge=0, le=100)
    warranty: float = Field(default=10, ge=0, le=100)
    past_rating: float = Field(default=10, ge=0, le=100)


class CopilotRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected|changes_requested)$")
    comment: str | None = Field(default=None, max_length=2000)


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(buyer|approver|admin)$")


class ContractCreateRequest(BaseModel):
    vendor_name: str = Field(min_length=2, max_length=255)
    title: str = Field(min_length=2, max_length=255)
    value: float = Field(default=0, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=20)
    start_date: str | None = None
    end_date: str | None = None
    terms: dict = Field(default_factory=dict)
