# Design Decision: WorkLog Settlement System Architecture

## 1. Architectural Philosophy
The system follows a **Domain-Driven Design (DDD)** approach, isolating logic into three distinct domains to manage complexity and ensure scalability:

*   **Tasks Domain**: Manages the "Proof of Work" (WorkLogs, TimeSegments, Tasks, Disputes).
*   **Financials Domain**: Manages the "Movement of Value" (Wallets, Remittances, Adjustments, Transactions).
*   **Users Domain**: Manages identity and role-based access (Workers vs. Admins).

This separation ensures that the Tasks domain remains agnostic of complex financial rules (tax, debt, liquidity), while the Financials domain acts as a governed state machine for value transfer.

---

## 2. Ensuring Financial Integrity (Handling Non-Immutability)
The system satisfies the constraint that historical data is not immutable through three primary mechanisms:

### A. Rate Snapshotting (`rate_at_recording`)
To prevent future Task rate changes from retroactively altering the value of work already performed, every `TimeSegment` captures the `rate_at_recording`.
*   **Why**: If a task rate increases from $50 to $60, work recorded yesterday must still be valued at $50. This preserves the financial "contract" at the time of execution.

### B. Delta Tracking (`last_settlement_run`)
`WorkLog` entities track the timestamp of their most recent successful settlement. 
*   **Why**: This allows the system to handle "Work Evolution" (additional segments added to old logs). The settlement query only picks up segments created or updated *after* the last run, ensuring no work is double-paid or ignored.

### C. The Adjustment Model
Retroactive quality issues or disputes are handled via the `Adjustment` model rather than mutating `SETTLED` segments.
*   **Why**: It creates a permanent audit trail. Deductions are queued as `PENDING` adjustments and resolved during the next settlement cycle.

---

## 3. The Settlement State Machine
The core of the system is the **Remittance Lifecycle**, which manages the transition from accrued earnings to finalized payouts.

| Status | Meaning | Fund Logic |
| :--- | :--- | :--- |
| `PENDING` | Created and awaiting the manual intervention window. | Moved from Admin `Balance` to `Reserve`. |
| `AWAITING_APPROVAL` | Paused/Stopped by an Admin during the delay window. | **Funds remain locked in Reserve.** Liability is preserved. |
| `AWAITING_FUNDING` | Blocked due to insufficient Admin balance. | **No fund movement.** Retried via periodic cron. |
| `OFFSET` | Earnings were used to pay off outstanding debt (Adjustments). | Net payout is $0. Funds remain in Admin `Balance`. |
| `COMPLETED` | Payout finalized and transferred to worker. | Moved from Admin `Reserve` to Worker `Balance`. |

### The "Pause" Logic (`AWAITING_APPROVAL`)
When an Admin "cancels" a payout during the `PENDING` delay window, the system transitions the remittance to `AWAITING_APPROVAL`.
*   **Consideration**: Since the underlying work (TimeSegments) has not been explicitly disputed or disqualified for quality issues, the liability remains valid.
*   **Resolution**: Instead of rolling back the funds to the Admin's spendable `Balance`, the money is **withheld in the Reserve**. This ensures the funds are "locked" and cannot be accidentally spent elsewhere, while preventing the automatic payout. The Admin must then explicitly "Approve" the record to release the funds to the worker.

---

## 4. Advanced Logic & Edge Cases

### A. The "Covered Adjustment" Rule (FIFO Debt Recovery)
To maintain a sane ledger, the system implements a strict rule: **Only link adjustments that current earnings can fully cover.**
*   **Logic**: During a settlement run, if a worker earns $100 but has a -$150 adjustment, the system recognizes it cannot fully clear the debt. 
*   **Outcome**: The $100 remittance is marked `OFFSET`, but the -$150 adjustment remains `PENDING`. This prevents "orphaned debt" and ensures that the next run will attempt to reclaim the remaining balance when more funds are available.

### B. Admin Fund Reservation (Liquidity Protection)
When a settlement is initiated, funds are immediately moved to a `Reserve` field in the Admin's wallet.
*   **Why**: This prevents the "Double Spend" problem. If a payout is delayed by 24 hours, the Admin cannot accidentally spend that same money on new tasks, ensuring the system remains solvent for its current liabilities.

### C. Accrued vs. Remitted Visibility
The `list-all-worklogs` endpoint supports an `includeAccrued=true` parameter.
*   **Remitted**: Value of segments with `SETTLED` status.
*   **Accrued**: Potential value of segments in `APPROVED` or `PENDING` states.
*   **Excluded**: `DISPUTED` or `REJECTED` segments are never included in financial totals until resolved.

---

## 5. Background Operations & Reconciliation

### Asynchronous Execution
The `/generate-remittances-for-all-users` endpoint is asynchronous. It returns a `task_id` linked to a `TaskStatus` model, allowing clients to poll for progress without blocking the request.

### Scheduled Jobs (The Financial Heartbeat)
*   **Phase A Reconciliation (Hourly)**: Scans for `PENDING` remittances older than the `REMITTANCE_DELAY_HOURS` (default 24h). It automatically finalizes the transfer from `Reserve` to the worker's wallet.
*   **Funding Retry (Every 30m)**: Scans for `AWAITING_FUNDING` records and attempts to process them if the Admin has since topped up their balance.
*   **Monthly Settlement (1st of month)**: Triggers a full system-wide settlement run.

---

## 6. Out of Scope / Limitations
*   **Phase B Reserve Audit**: The current implementation does not perform a secondary validation to ensure the `Wallet.reserve` total mathematically equals the sum of all `PENDING` remittances. This is intended for Reconciliation.       
*   **Multi-Currency Conversion**: While the schema supports a `currency` field, the settlement logic assumes all calculations occur in the wallet's base currency intentionally to limit the implementation scope (defaulting to USD). 
*   **Partial Adjustment Clearing**: Adjustments are currently binary (PENDING or PAID). They are not partially cleared; they wait for a remittance that can cover the full amount of that specific adjustment.
