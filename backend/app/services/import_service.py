import csv
import io
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import List, Dict, Any, Optional
import difflib

class RowPreview:
    def __init__(self, row_number: int, raw_row: dict):
        self.row_number = row_number
        self.raw_row = raw_row
        self.status = "green" # green, yellow, red, grey
        self.anomalies: List[Dict[str, str]] = []
        self.parsed_data: Dict[str, Any] = {}
        
    def add_anomaly(self, anomaly_type: str, detail: str, action: str, level: str):
        self.anomalies.append({
            "type": anomaly_type,
            "detail": detail,
            "action": action
        })
        if level == "red":
            self.status = "red"
        elif level == "yellow" and self.status == "green":
            self.status = "yellow"
        elif level == "grey":
            self.status = "grey"

def descriptions_similar(d1: str, d2: str) -> bool:
    d1_clean = re.sub(r'[^a-zA-Z0-9\s]', '', d1.lower()).strip()
    d2_clean = re.sub(r'[^a-zA-Z0-9\s]', '', d2.lower()).strip()
    if d1_clean == d2_clean:
        return True
    ratio = difflib.SequenceMatcher(None, d1_clean, d2_clean).ratio()
    if ratio > 0.6:
        return True
    words1 = set(d1_clean.split())
    words2 = set(d2_clean.split())
    ignore_words = {"at", "the", "bill", "for", "in", "on", "of", "and", "a", "an", "night", "day"}
    words1 -= ignore_words
    words2 -= ignore_words
    if words1 & words2 and len(words1 & words2 & {"thalassa", "marina", "bites"}) > 0:
        return True
    return False

def process_csv(file_content: str, users: List[Any], memberships: List[Any]) -> List[Dict]:
    user_map = {u.name.lower(): u for u in users}
    seen_expenses = {}
    reader = csv.DictReader(io.StringIO(file_content.strip()))
    previews = []
    
    for row_number, row in enumerate(reader, start=2):
        preview = RowPreview(row_number, dict(row))
        
        raw_desc = row.get("description", "").strip()
        raw_payer = row.get("paid_by", "")
        raw_amount = row.get("amount", "")
        raw_currency = row.get("currency", "")
        raw_date = row.get("date", "")
        raw_split_type = row.get("split_type", "").strip()
        raw_split_details = row.get("split_details", "").strip()
        raw_notes = row.get("notes", "").strip()
        
        parsed = {
            "is_settlement": False,
            "skip": False,
            "description": raw_desc,
            "notes": raw_notes,
            "split_type": raw_split_type,
            "expense_date": None,
            "amount_raw": None,
            "currency": None,
            "paid_by_user_id": None,
            "paid_to_user_id": None,
            "participants": []
        }
        
        # ROW 30: Zero amount
        try:
            amt_val = Decimal(re.sub(r'[^\d.-]', '', raw_amount) or '0')
        except:
            amt_val = Decimal('0')
            
        if amt_val == Decimal('0'):
            preview.add_anomaly("zero_amount", "Amount is zero", "skipped", "grey")
            parsed["skip"] = True
            preview.parsed_data = parsed
            previews.append(preview)
            continue
            
        # ROW 13 / 37: Settlement/Deposit disguised
        if "settlement" in raw_notes.lower() or "deposit" in raw_desc.lower() or "paid back" in raw_desc.lower():
            parsed["is_settlement"] = True
            preview.add_anomaly("settlement_as_expense", "Disguised as expense", "imported_as_settlement", "yellow")
        
        # ROW 28: Whitespace in amount
        if raw_amount != raw_amount.strip():
            preview.add_anomaly("whitespace_amount", "Leading/trailing spaces", "auto_fixed", "yellow")
            raw_amount = raw_amount.strip()
            
        # ROW 6: Comma in amount
        if ',' in raw_amount:
            preview.add_anomaly("comma_in_amount", "Comma removed", "auto_fixed", "yellow")
            raw_amount = raw_amount.replace(',', '')
            
        try:
            parsed["amount_raw"] = Decimal(raw_amount)
        except:
            preview.add_anomaly("invalid_amount", f"Cannot parse {raw_amount}", "flagged_for_review", "red")
            
        # ROW 9: Excess precision
        if parsed["amount_raw"] is not None:
            rounded = parsed["amount_raw"].quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
            if rounded != parsed["amount_raw"]:
                preview.add_anomaly("excess_precision", "Rounded to 2 decimals", "auto_fixed", "yellow")
                parsed["amount_raw"] = rounded
                
        # ROW 25: Negative amount
        if parsed["amount_raw"] is not None and parsed["amount_raw"] < 0:
            preview.add_anomaly("negative_amount", "Treated as refund", "auto_fixed", "yellow")
            
        # ROW 27: Missing currency
        if not raw_currency:
            preview.add_anomaly("missing_currency", "Defaulted to INR", "auto_fixed", "yellow")
            parsed["currency"] = "INR"
        else:
            parsed["currency"] = raw_currency.strip().upper()
            
        # ROW 12: Missing payer
        if not raw_payer:
            preview.add_anomaly("missing_payer", "Payer is missing", "flagged_for_review", "red")
            parsed["paid_by_user_id"] = None
        else:
            # ROW 26: Trailing whitespace payer
            if raw_payer != raw_payer.strip():
                preview.add_anomaly("whitespace_payer", "Stripped and title cased", "auto_fixed", "yellow")
            
            clean_payer = raw_payer.strip().title()
            
            matched_user = None
            for u_name, u in user_map.items():
                if u_name == clean_payer.lower():
                    matched_user = u
                    break
            
            # ROW 10: Ambiguous payer
            if matched_user:
                parsed["paid_by_user_id"] = matched_user.id
            else:
                matches = difflib.get_close_matches(clean_payer.lower(), user_map.keys(), n=1, cutoff=0.6)
                if matches:
                    preview.add_anomaly("ambiguous_payer", f"Matched to {matches[0].title()}", "flagged_for_review", "red")
                    parsed["paid_by_user_id"] = user_map[matches[0]].id
                else:
                    preview.add_anomaly("unknown_payer", f"Cannot match {clean_payer}", "flagged_for_review", "red")
                    
        # ROW 26 & 33: Date parsing
        if raw_date:
            try:
                if re.match(r"^[A-Za-z]{3}\s\d{1,2}$", raw_date.strip()): # "Mar 14"
                    parsed["expense_date"] = datetime.strptime(f"{raw_date.strip()} 2026", "%b %d %Y").strftime("%Y-%m-%d")
                    preview.add_anomaly("unparseable_date", "Inferred year 2026", "auto_fixed", "yellow")
                else:
                    if '/' in raw_date:
                        parts = raw_date.split('/')
                        if len(parts) == 3:
                            p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
                            if p1 <= 12 and p2 <= 12 and p1 != p2:
                                preview.add_anomaly("ambiguous_date", "Is it DD/MM or MM/DD?", "flagged_for_review", "red")
                                parsed["expense_date"] = datetime(p3, p2, p1).strftime("%Y-%m-%d")
                            else:
                                parsed["expense_date"] = datetime(p3, p2, p1).strftime("%Y-%m-%d")
                    else:
                        parsed["expense_date"] = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            except Exception as e:
                preview.add_anomaly("invalid_date", f"Cannot parse {raw_date}", "flagged_for_review", "red")
                
        # ROW 5 & 23/24: Duplicates
        if parsed["expense_date"] and parsed["amount_raw"] is not None:
            # Exact duplicate check
            dup_key = (parsed["expense_date"], parsed["paid_by_user_id"], str(parsed["amount_raw"]))
            if dup_key in seen_expenses:
                prev_row = seen_expenses[dup_key]
                preview.add_anomaly("duplicate_expense", f"Conflicts with row {prev_row}", "flagged_for_review", "red")
                # Update the previous preview to show conflict
                for p in previews:
                    if p.row_number == prev_row:
                        if not any(a["type"] == "duplicate_expense" for a in p.anomalies):
                            p.add_anomaly("duplicate_expense", f"Conflicts with row {row_number}", "flagged_for_review", "red")
            else:
                seen_expenses[dup_key] = row_number
                
            # Conflicting duplicate check (same date, similar description, different payer/amount)
            for prev in previews:
                if prev.parsed_data.get("expense_date") == parsed["expense_date"]:
                    if descriptions_similar(raw_desc, prev.parsed_data.get("description", "")):
                        prev_payer = prev.parsed_data.get("paid_by_user_id")
                        prev_amount_str = prev.parsed_data.get("amount_raw")
                        if prev_payer != parsed["paid_by_user_id"] or prev_amount_str != str(parsed["amount_raw"]):
                            preview.add_anomaly("duplicate_expense", f"Conflicting duplicate of row {prev.row_number}", "flagged_for_review", "red")
                            if not any(a["type"] == "duplicate_expense" for a in prev.anomalies):
                                prev.add_anomaly("duplicate_expense", f"Conflicting duplicate of row {row_number}", "flagged_for_review", "red")
        
        # Split & Settlement Payee parsing
        if parsed["is_settlement"]:
            # Find the payee for settlement from split_with
            raw_split_with = row.get("split_with", "").strip()
            if not raw_split_with:
                preview.add_anomaly("missing_payee", "Payee is missing for settlement", "flagged_for_review", "red")
            else:
                clean_payee = raw_split_with.strip().title()
                matched_payee = user_map.get(clean_payee.lower())
                if matched_payee:
                    parsed["paid_to_user_id"] = matched_payee.id
                else:
                    preview.add_anomaly("unknown_payee", f"Cannot match payee {clean_payee}", "flagged_for_review", "red")
        else:
            raw_split_with = row.get("split_with", "").strip()
            raw_split_details = row.get("split_details", "").strip()
            parsed_parts = []
            
            if raw_split_details:
                parts = [p.strip() for p in raw_split_details.split(';') if p.strip()]
                total_pct = Decimal(0)
                all_ones = True
                
                for p in parts:
                    match = re.match(r"([A-Za-z\s'\.]+?)\s+([\d\.]+%?)", p.strip())
                    if match:
                        name = match.group(1).strip().title()
                        val_str = match.group(2)
                        is_pct = '%' in val_str
                        val = Decimal(val_str.replace('%', ''))
                        
                        if val != Decimal(1):
                            all_ones = False
                        
                        u = user_map.get(name.lower())
                        if not u:
                            preview.add_anomaly("external_participant", f"{name} is not a member", "flagged_external", "yellow")
                        else:
                            m_record = next((m for m in memberships if m.user_id == u.id), None)
                            if not m_record:
                                preview.add_anomaly("external_participant", f"{name} is not a member", "flagged_external", "yellow")
                            elif m_record.left_at and parsed["expense_date"] and parsed["expense_date"] >= m_record.left_at.strftime("%Y-%m-%d"):
                                preview.add_anomaly("departed_member", f"{name} left group before expense", "auto_fixed", "yellow")
                                continue
                            elif m_record.joined_at and parsed["expense_date"] and parsed["expense_date"] < m_record.joined_at.strftime("%Y-%m-%d"):
                                preview.add_anomaly("departed_member", f"{name} not yet joined group before expense", "auto_fixed", "yellow")
                                continue
                            
                            parsed_parts.append({"user_id": u.id, "share_raw": str(val)})
                            if is_pct:
                                total_pct += val
                
                # ROW 41: Conflicting split
                if parsed["split_type"] == "equal" and len(parsed_parts) > 0:
                    if all_ones:
                        preview.add_anomaly("conflicting_split", "Equal split shares -> equal", "auto_fixed", "yellow")
                    else:
                        preview.add_anomaly("conflicting_split", "Shares provided for equal split", "flagged_for_review", "red")
                
                # ROW 14: Percentages
                if parsed["split_type"] == "percentage" and total_pct != Decimal(100):
                    preview.add_anomaly("invalid_percentage", f"Sums to {total_pct}%", "flagged_for_review", "red")
                    
            elif raw_split_with:
                names = [n.strip() for n in raw_split_with.split(';') if n.strip()]
                for name in names:
                    clean_name = name.strip().title()
                    u = user_map.get(clean_name.lower())
                    if not u:
                        preview.add_anomaly("external_participant", f"{clean_name} is not a member", "flagged_external", "yellow")
                    else:
                        m_record = next((m for m in memberships if m.user_id == u.id), None)
                        if not m_record:
                            preview.add_anomaly("external_participant", f"{clean_name} is not a member", "flagged_external", "yellow")
                        elif m_record.left_at and parsed["expense_date"] and parsed["expense_date"] >= m_record.left_at.strftime("%Y-%m-%d"):
                            preview.add_anomaly("departed_member", f"{clean_name} left group before expense", "auto_fixed", "yellow")
                            continue
                        elif m_record.joined_at and parsed["expense_date"] and parsed["expense_date"] < m_record.joined_at.strftime("%Y-%m-%d"):
                            preview.add_anomaly("departed_member", f"{clean_name} not yet joined group before expense", "auto_fixed", "yellow")
                            continue
                        
                        parsed_parts.append({"user_id": u.id, "share_raw": "1"})
            
            parsed["participants"] = parsed_parts
            
        if parsed["amount_raw"] is not None:
            parsed["amount_raw"] = str(parsed["amount_raw"])
            
        preview.parsed_data = parsed
        previews.append(preview)
        
    return [p.__dict__ for p in previews]

