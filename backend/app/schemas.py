from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

# --- Users ---
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Groups ---
class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

class GroupMembershipBase(BaseModel):
    group_id: int
    user_id: int

class GroupMembershipResponse(GroupMembershipBase):
    id: int
    joined_at: datetime
    left_at: Optional[datetime] = None
    class Config:
        orm_mode = True

# --- Expenses ---
class ExpenseParticipantBase(BaseModel):
    user_id: int
    share_raw: Optional[Decimal] = None 
    share_amount_inr: Optional[Decimal] = None 

class ExpenseCreate(BaseModel):
    group_id: int
    description: str
    expense_date: date
    amount_raw: Decimal 
    currency: str 
    paid_by_user_id: Optional[int] = None
    split_type: str # 'equal', 'unequal', 'percentage', 'share'
    participants: List[ExpenseParticipantBase]

class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    description: str
    paid_by_user_id: Optional[int]
    amount_inr: Decimal
    original_amount: Decimal
    original_currency: str
    usd_rate_used: Optional[Decimal]
    split_type: str
    expense_date: date
    is_deleted: bool
    import_row_number: Optional[int]
    created_at: datetime
    class Config:
        orm_mode = True

# --- Settlements ---
class SettlementCreate(BaseModel):
    group_id: int
    paid_by_user_id: int
    paid_to_user_id: int
    amount_inr: Decimal
    settlement_date: date
    notes: Optional[str] = None

class SettlementResponse(BaseModel):
    id: int
    group_id: int
    paid_by_user_id: int
    paid_to_user_id: int
    amount_inr: Decimal
    settlement_date: date
    notes: Optional[str]
    created_at: datetime
    class Config:
        orm_mode = True

# --- Balances ---
class BalanceSummary(BaseModel):
    user_id: int
    net_balance: Decimal

class DebtSimplification(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: Decimal
