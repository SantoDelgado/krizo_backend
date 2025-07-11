from pydantic import BaseModel, constr
from typing import Optional, List
from datetime import datetime
from database.models import PromotionType, PromotionStatus

class PromotionBase(BaseModel):
    name: str
    description: str
    type: PromotionType
    value: float
    min_purchase: Optional[float] = None
    max_discount: Optional[float] = None
    start_date: datetime
    end_date: datetime
    code: str
    usage_limit: Optional[int] = None

class PromotionCreate(PromotionBase):
    pass

class Promotion(PromotionBase):
    id: int
    business_profile_id: int
    status: PromotionStatus
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class PromotionRedemptionBase(BaseModel):
    promotion_id: int
    amount_saved: float

class PromotionRedemptionCreate(PromotionRedemptionBase):
    pass

class PromotionRedemption(PromotionRedemptionBase):
    id: int
    user_id: int
    transaction_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class LoyaltyProgramBase(BaseModel):
    name: str
    description: str
    points_per_currency: float
    min_points_redemption: int
    points_value: float

class LoyaltyProgramCreate(LoyaltyProgramBase):
    pass

class LoyaltyProgram(LoyaltyProgramBase):
    id: int
    business_profile_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class LoyaltyMemberBase(BaseModel):
    points_balance: int
    total_points_earned: int
    total_points_redeemed: int
    tier: str

class LoyaltyMemberCreate(LoyaltyMemberBase):
    loyalty_program_id: int

class LoyaltyMember(LoyaltyMemberBase):
    id: int
    loyalty_program_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class LoyaltyTransactionBase(BaseModel):
    points: int
    type: str
    description: str

class LoyaltyTransactionCreate(LoyaltyTransactionBase):
    loyalty_member_id: int
    transaction_id: int

class LoyaltyTransaction(LoyaltyTransactionBase):
    id: int
    loyalty_member_id: int
    transaction_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class PromotionResponse(BaseModel):
    promotion: Promotion
    amount_saved: float
    final_amount: float

class LoyaltyPointsResponse(BaseModel):
    points_earned: int
    new_balance: int
    tier: str 