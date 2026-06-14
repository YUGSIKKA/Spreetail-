# Architectural Decisions

- **USD conversion**: Used a fixed rate (`84.0 INR/USD`) rather than a live API to ensure historical accuracy, determinism, and to avoid external dependency failures during file import.
- **Negative amounts**: Treated as refunds (deducting from owed balances) rather than errors because genuine refunds occur (e.g. cancelled tickets) and re-splitting them correctly offsets debts.
- **Duplicate resolution**: Chose user-approval over auto-dropping. In shared expenses, identically priced items on the same day can happen legitimately (e.g., buying two identical rounds of drinks separately).
- **Debt simplification**: Implemented a pure `min-cash-flow` algorithm rather than pairwise settlement. This drastically reduces the total number of transactions needed to settle up a group.
- **Rounding**: Adopted banker's rounding (`ROUND_HALF_EVEN`) via Python's `quantize()` to minimize cumulative rounding bias over hundreds of expenses.
- **Meera post-departure**: Automatically removed departed members from subsequent equal splits and redistributed their share. It's logically inconsistent for a departed member to accrue new debts.
- **Zero-amount expense**: Skipped instead of imported because zero-value entries add noise to the database and UI without affecting actual balances.
