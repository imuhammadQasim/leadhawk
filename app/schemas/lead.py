
#ye lead.py schema file hai. Iska kaam Lead API ke request aur response ka structure define karna hai.
from datetime import datetime

from pydantic import BaseModel, Field


class LeadGenerateRequest(BaseModel):
    city: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=255)


class LeadResponse(BaseModel):
    id: int
    source: str
    business_name: str
    category: str
    city: str
    address: str | None
    phone: str | None
    website: str | None
    rating: float | None
    review_count: int | None
    owner_name: str | None
    owner_email: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class LeadGenerateResponse(BaseModel):
    code: int
    success: bool
    message: str
    count: int
    leads: list[LeadResponse]
