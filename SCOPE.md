# App Scope and Specifications

## Database Schema
- **users**: id, name, email, hashed_password, created_at
- **groups**: id, name, created_at
- **group_memberships**: id, group_id, user_id, joined_at, left_at
- **expenses**: id, group_id, description, paid_by_user_id, amount_inr, original_amount, original_currency, usd_rate_used, split_type, expense_date, is_deleted, import_row_number, created_at
- **expense_participants**: id, expense_id, user_id, share_amount_inr, share_raw, created_at
- **settlements**: id, group_id, paid_by_user_id, paid_to_user_id, amount_inr, settlement_date, notes, created_at
- **import_sessions**: id, filename, imported_at, imported_by_user_id, total_rows, imported_count, flagged_count, skipped_count
- **import_anomalies**: id, import_session_id, row_number, raw_row, anomaly_type, anomaly_detail, action_taken, resolution, approved_by_user_id, approved_at

## Anomaly Matrix

| Row | Type | Description | Policy | Action |
|-----|------|-------------|--------|--------|
| 5 | EXACT DUPLICATE | Exact duplicate of row 4 | Flag both, keep first by default | `flagged_for_review` |
| 6 | COMMA IN AMOUNT | `1,200` | Strip commas | `imported_with_fix` |
| 9 | EXCESS DECIMAL | `899.995` | Banker's rounding to 2 places | `imported_with_fix` |
| 10 | AMBIGUOUS PAYER | "Priya S" | Fuzzy match, flag for approval | `flagged_for_review` |
| 12 | MISSING PAYER | Empty payer | Set NULL, flag UNRESOLVED | `flagged_for_review` |
| 13 | SETTLEMENT DISGUISED | "Rohan paid Aisha back" | Import as settlement | `imported_with_fix` |
| 14 | PERCENTAGES != 100 | Sums to 110% | Flag for user approval | `flagged_for_review` |
| 22 | NON-MEMBER IN SPLIT | "Dev's friend Kabir" | Map to non-member/flag | `flagged_external` |
| 23/24 | CONFLICTING DUPLICATE | Same dinner, diff amount | Flag both | `flagged_for_review` |
| 25 | NEGATIVE AMOUNT | Refund | Keep as refund | `imported_with_fix` |
| 26 | UNPARSEABLE DATE | "Mar 14" | Infer year as 2026 | `imported_with_fix` |
| 26 | TRAILING WHITESPACE | "rohan " | Strip & title case | `imported_with_fix` |
| 27 | MISSING CURRENCY | empty | Default to INR | `imported_with_fix` |
| 28 | WHITESPACE AMOUNT | " 1450 " | Strip | `imported_with_fix` |
| 30 | ZERO AMOUNT | 0 | Skip entirely | `skipped` |
| 33 | AMBIGUOUS DATE | 04/05/2026 | Flag for DD/MM vs MM/DD | `flagged_for_review` |
| 35 | DEPARTED MEMBER | Left before expense | Remove & redistribute | `imported_with_fix` |
| 37 | DEPOSIT DISGUISED | "Sam deposit share" | Import as settlement | `imported_with_fix` |
| 41 | CONFLICTING SPLIT | Equal type, details present | Import as equal if uniform | `imported_with_fix` |
