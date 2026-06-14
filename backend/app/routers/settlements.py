from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app import schemas, models
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.post("/", response_model=schemas.SettlementResponse)
async def create_settlement(settlement: schemas.SettlementCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Records a payment between two members."""
    # Ensure current user is involved
    if settlement.paid_by_user_id != current_user.id and settlement.paid_to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only record settlements involving yourself")
        
    db_settlement = models.Settlement(
        group_id=settlement.group_id,
        paid_by_user_id=settlement.paid_by_user_id,
        paid_to_user_id=settlement.paid_to_user_id,
        amount_inr=settlement.amount_inr,
        settlement_date=settlement.settlement_date,
        notes=settlement.notes
    )
    db.add(db_settlement)
    await db.commit()
    await db.refresh(db_settlement)
    
    return db_settlement

@router.get("/group/{group_id}", response_model=List[schemas.SettlementResponse])
async def get_settlements(group_id: int, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Retrieves all settlements for a group."""
    stmt = select(models.GroupMembership).where(models.GroupMembership.group_id == group_id, models.GroupMembership.user_id == current_user.id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this group")
        
    stmt = select(models.Settlement).where(models.Settlement.group_id == group_id).order_by(models.Settlement.settlement_date.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
