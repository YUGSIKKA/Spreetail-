from decimal import Decimal
from typing import List, Dict
from app.schemas import DebtSimplification

def simplify_debts(balances: Dict[int, Decimal]) -> List[DebtSimplification]:
    """
    A pure function to simplify debts using the minimum cash flow algorithm.
    Takes a dict of {user_id: net_balance} and returns minimal transactions.
    """
    debtors = []
    creditors = []
    
    for user_id, balance in balances.items():
        if balance < Decimal("0.00"):
            debtors.append([user_id, balance])
        elif balance > Decimal("0.00"):
            creditors.append([user_id, balance])
            
    debtors.sort(key=lambda x: x[1]) # Most negative first
    creditors.sort(key=lambda x: x[1], reverse=True) # Most positive first
    
    transactions = []
    
    i = 0
    j = 0
    
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]
        
        settle_amount = min(abs(debt), credit)
        
        # ensure we round to 2 decimals
        settle_amount = round(settle_amount, 2)
        
        if settle_amount > Decimal("0.00"):
            transactions.append(
                DebtSimplification(
                    from_user_id=debtor_id,
                    to_user_id=creditor_id,
                    amount=settle_amount
                )
            )
        
        debtors[i][1] += settle_amount
        creditors[j][1] -= settle_amount
        
        if abs(debtors[i][1]) < Decimal("0.01"):
            i += 1
        if abs(creditors[j][1]) < Decimal("0.01"):
            j += 1
            
    return transactions
