from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
from decimal import Decimal

from app import schemas, models
from app.database import get_db
from app.routers.auth import get_current_user
from app.services.balance_service import simplify_debts

router = APIRouter(prefix="/balances", tags=["balances"])

@router.get("/group/{group_id}", response_model=List[schemas.DebtSimplification])
async def get_simplified_balances(group_id: int, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Returns minimum cash flow transactions to settle all debts in a group."""
    stmt = select(models.GroupMembership).where(models.GroupMembership.group_id == group_id, models.GroupMembership.user_id == current_user.id, models.GroupMembership.left_at.is_(None))
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not an active member of this group")

    # Get active members
    members_stmt = select(models.GroupMembership.user_id).where(models.GroupMembership.group_id == group_id, models.GroupMembership.left_at.is_(None))
    result = await db.execute(members_stmt)
    active_member_ids = set(result.scalars().all())
    
    balances: Dict[int, Decimal] = {m: Decimal("0.00") for m in active_member_ids}
    
    expenses_stmt = select(models.Expense).where(models.Expense.group_id == group_id, models.Expense.is_deleted == False)
    result = await db.execute(expenses_stmt)
    expenses = result.scalars().all()
    
    for expense in expenses:
        if expense.paid_by_user_id and expense.paid_by_user_id in balances:
            balances[expense.paid_by_user_id] += expense.amount_inr
            
        parts_stmt = select(models.ExpenseParticipant).where(models.ExpenseParticipant.expense_id == expense.id)
        parts_result = await db.execute(parts_stmt)
        participants = parts_result.scalars().all()
        
        for p in participants:
            if p.user_id in balances:
                balances[p.user_id] -= p.share_amount_inr
                
    settlements_stmt = select(models.Settlement).where(models.Settlement.group_id == group_id)
    settlements_result = await db.execute(settlements_stmt)
    settlements = settlements_result.scalars().all()
    
    for s in settlements:
        if s.paid_by_user_id in balances:
            balances[s.paid_by_user_id] += s.amount_inr
        if s.paid_to_user_id in balances:
            balances[s.paid_to_user_id] -= s.amount_inr
            
    balances = {k: v for k, v in balances.items() if abs(v) > Decimal("0.01")}
    transactions = simplify_debts(balances)
    return transactions
