from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app import schemas, models
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/", response_model=schemas.GroupResponse)
async def create_group(group: schemas.GroupCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Creates a new group and adds the current user as an active member."""
    db_group = models.Group(name=group.name)
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    
    db_membership = models.GroupMembership(group_id=db_group.id, user_id=current_user.id)
    db.add(db_membership)
    await db.commit()
    
    return db_group

@router.get("/", response_model=List[schemas.GroupResponse])
async def list_groups(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Lists all groups the current user is a member of."""
    stmt = select(models.Group).join(models.GroupMembership).where(models.GroupMembership.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{group_id}/members", response_model=schemas.GroupMembershipResponse)
async def add_member(group_id: int, user_id: int, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Adds a user to a group."""
    stmt = select(models.GroupMembership).where(models.GroupMembership.group_id == group_id, models.GroupMembership.user_id == current_user.id, models.GroupMembership.left_at.is_(None))
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not an active member of this group")
        
    db_membership = models.GroupMembership(group_id=group_id, user_id=user_id)
    db.add(db_membership)
    await db.commit()
    await db.refresh(db_membership)
    return db_membership
