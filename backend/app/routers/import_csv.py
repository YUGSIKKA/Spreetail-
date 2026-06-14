from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import json

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user
from app.services.import_service import process_csv

router = APIRouter(prefix="/import", tags=["import"])

@router.post("/preview")
async def preview_csv(
    group_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Processes uploaded CSV and returns preview mapping showing 3-color status for anomalies."""
    content = await file.read()
    text_content = content.decode("utf-8")
    
    users = (await db.execute(select(models.User))).scalars().all()
    memberships = (await db.execute(select(models.GroupMembership).where(models.GroupMembership.group_id == group_id))).scalars().all()
    
    previews = process_csv(text_content, users, memberships)
    return {"previews": previews}

@router.post("/commit")
async def commit_import(
    payload: Dict[str, Any],
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Commits user-approved rows into the database and generates ImportSession."""
    from decimal import Decimal, ROUND_HALF_EVEN
    from datetime import datetime
    
    group_id = payload.get("group_id")
    previews = payload.get("previews", [])
    rows = payload.get("rows", [])
    
    # Normalize input
    items_to_process = []
    if previews:
        for p in previews:
            parsed = p.get("parsed_data")
            if parsed and not parsed.get("skip"):
                items_to_process.append({
                    "parsed": parsed,
                    "row_number": p.get("row_number"),
                    "raw_row": p.get("raw_row"),
                    "anomalies": p.get("anomalies", [])
                })
    elif rows:
        for idx, r in enumerate(rows):
            if not r.get("skip"):
                items_to_process.append({
                    "parsed": r,
                    "row_number": idx + 2,
                    "raw_row": {},
                    "anomalies": []
                })
                
    # Create the ImportSession
    total_rows = len(previews) if previews else len(rows)
    skipped_count = len([p for p in previews if p.get("parsed_data", {}).get("skip")]) if previews else len([r for r in rows if r.get("skip")])
    flagged_count = len([p for p in previews if len(p.get("anomalies", [])) > 0 and not p.get("parsed_data", {}).get("skip")]) if previews else 0
    imported_count = len(items_to_process)
    
    session = models.ImportSession(
        filename="import.csv",
        imported_by_user_id=current_user.id,
        total_rows=total_rows,
        imported_count=imported_count,
        flagged_count=flagged_count,
        skipped_count=skipped_count
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Process and insert each item
    for item in items_to_process:
        parsed = item["parsed"]
        row_number = item["row_number"]
        
        # Save anomalies
        for anomaly in item["anomalies"]:
            db_anomaly = models.ImportAnomaly(
                import_session_id=session.id,
                row_number=row_number,
                raw_row=json.dumps(item["raw_row"]),
                anomaly_type=anomaly["type"],
                anomaly_detail=anomaly["detail"],
                action_taken=anomaly["action"],
                resolution="Auto-resolved/Fixed",
                approved_by_user_id=current_user.id,
                approved_at=datetime.utcnow()
            )
            db.add(db_anomaly)
            
        if parsed.get("is_settlement"):
            # Insert Settlement
            settlement_date_str = parsed.get("expense_date")
            settlement_date = datetime.strptime(settlement_date_str, "%Y-%m-%d").date() if settlement_date_str else datetime.utcnow().date()
            
            db_settlement = models.Settlement(
                group_id=group_id,
                paid_by_user_id=parsed.get("paid_by_user_id"),
                paid_to_user_id=parsed.get("paid_to_user_id"),
                amount_inr=Decimal(parsed.get("amount_raw")),
                settlement_date=settlement_date,
                notes=parsed.get("notes") or parsed.get("description")
            )
            db.add(db_settlement)
        else:
            # Insert Expense
            expense_date_str = parsed.get("expense_date")
            expense_date = datetime.strptime(expense_date_str, "%Y-%m-%d").date() if expense_date_str else datetime.utcnow().date()
            
            original_amount = Decimal(parsed.get("amount_raw"))
            original_currency = parsed.get("currency", "INR")
            
            # USD to INR conversion
            usd_rate = Decimal("84.0") if original_currency == "USD" else None
            amount_inr = original_amount * usd_rate if original_currency == "USD" else original_amount
            amount_inr = amount_inr.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
            
            db_expense = models.Expense(
                group_id=group_id,
                description=parsed.get("description"),
                paid_by_user_id=parsed.get("paid_by_user_id"),
                original_amount=original_amount,
                original_currency=original_currency,
                usd_rate_used=usd_rate,
                amount_inr=amount_inr,
                split_type=parsed.get("split_type"),
                expense_date=expense_date,
                is_deleted=False,
                import_row_number=row_number,
                notes=parsed.get("notes")
            )
            db.add(db_expense)
            await db.commit() # Commit to get db_expense.id
            await db.refresh(db_expense)
            
            # Insert Expense Participants
            participants = parsed.get("participants", [])
            split_type = parsed.get("split_type")
            
            if participants:
                # 1. Compute unrounded share amounts in INR
                shares_inr = []
                if split_type == "equal":
                    n_parts = len(participants)
                    share_val = amount_inr / n_parts
                    for p in participants:
                        shares_inr.append((p["user_id"], share_val, Decimal(p["share_raw"])))
                elif split_type == "percentage":
                    for p in participants:
                        share_val = amount_inr * (Decimal(p["share_raw"]) / Decimal("100.0"))
                        shares_inr.append((p["user_id"], share_val, Decimal(p["share_raw"])))
                elif split_type == "share":
                    total_weight = sum(Decimal(p["share_raw"]) for p in participants)
                    for p in participants:
                        share_val = amount_inr * (Decimal(p["share_raw"]) / total_weight)
                        shares_inr.append((p["user_id"], share_val, Decimal(p["share_raw"])))
                elif split_type == "unequal":
                    for p in participants:
                        share_val = Decimal(p["share_raw"]) * Decimal("84.0") if original_currency == "USD" else Decimal(p["share_raw"])
                        shares_inr.append((p["user_id"], share_val, Decimal(p["share_raw"])))
                else:
                    # Fallback equal
                    n_parts = len(participants)
                    share_val = amount_inr / n_parts
                    for p in participants:
                        shares_inr.append((p["user_id"], share_val, Decimal(p["share_raw"])))
                        
                # 2. Round each participant's share using ROUND_HALF_EVEN
                rounded_shares = []
                for user_id, share_val, share_raw in shares_inr:
                    rounded_val = share_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
                    rounded_shares.append({
                        "user_id": user_id,
                        "share_amount_inr": rounded_val,
                        "share_raw": share_raw
                    })
                    
                # 3. Adjust for any tiny rounding discrepancy (distribute to first participant)
                sum_rounded = sum(s["share_amount_inr"] for s in rounded_shares)
                diff = amount_inr - sum_rounded
                if diff != Decimal("0.00") and len(rounded_shares) > 0:
                    rounded_shares[0]["share_amount_inr"] += diff
                    
                # 4. Insert into database
                for s in rounded_shares:
                    db_participant = models.ExpenseParticipant(
                        expense_id=db_expense.id,
                        user_id=s["user_id"],
                        share_amount_inr=s["share_amount_inr"],
                        share_raw=s["share_raw"]
                    )
                    db.add(db_participant)
                    
    await db.commit()
    return {"status": "success", "session_id": session.id}

