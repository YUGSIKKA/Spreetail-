from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from decimal import Decimal

from app import schemas, models
from app.database import get_db
from app.routers.auth import get_current_user
from app.services.currency_service import convert_to_inr

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("/", response_model=schemas.ExpenseResponse)
async def create_expense(expense: schemas.ExpenseCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Creates a new shared expense and calculates individual shares based on split_type."""
    amount_inr, usd_rate_used = convert_to_inr(expense.amount_raw, expense.currency)
    
    total_share_raw = sum([p.share_raw or Decimal("0") for p in expense.participants])
    
    db_expense = models.Expense(
        group_id=expense.group_id,
        description=expense.description,
        paid_by_user_id=expense.paid_by_user_id,
        amount_inr=amount_inr,
        original_amount=expense.amount_raw,
        original_currency=expense.currency,
        usd_rate_used=usd_rate_used,
        split_type=expense.split_type,
        expense_date=expense.expense_date
    )
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    
    for p in expense.participants:
        share_inr = Decimal("0")
        if expense.split_type == 'equal':
            share_inr = amount_inr / Decimal(str(len(expense.participants)))
        elif expense.split_type == 'percentage':
            share_inr = amount_inr * (p.share_raw / Decimal("100"))
        elif expense.split_type == 'share':
            share_inr = amount_inr * (p.share_raw / total_share_raw)
        elif expense.split_type == 'unequal':
            share_inr = p.share_raw 
            
        share_inr = round(share_inr, 2)
            
        db_p = models.ExpenseParticipant(
            expense_id=db_expense.id,
            user_id=p.user_id,
            share_amount_inr=share_inr,
            share_raw=p.share_raw
        )
        db.add(db_p)
        
    await db.commit()
    return db_expense
