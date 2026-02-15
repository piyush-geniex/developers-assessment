# WorkLog Settlement E2E Test Cases

This file defines practical API test cases for the constraints in `backend.md`.
After running the stack, apply migrations and execute curl requests, mark each case as `PASSED` or `FAILED`.

## Environment Prep

1. Start services:
   - `docker compose up`
2. Apply migrations in backend container:
   - `alembic upgrade head`
3. Use API base:
   - `http://localhost:8000/api/v1`

## Status Legend

- `PENDING`: not executed yet
- `PASSED`: behavior matches expected result
- `FAILED`: behavior does not match expected result

---

## Test Case 1: Basic Strict Period Remittance (Success)

**Constraints covered**
- settlement over a period
- remittance generation

**Setup**
- Create one user with one worklog.
- Add one `worklog_entry` in period `2026-01-01` to `2026-01-31` with amount `100.00`.

**Request**
- `POST /generate-remittances-for-all-users`
- Body:
  - `from_date: 2026-01-01`
  - `to_date: 2026-01-31`
  - `idempotency_key: tc1_run_001`
- Header:
  - `X-Payout-Mode: success`

**Expected**
- `run_status = COMPLETED`
- `remitted_count >= 1`
- `failed_count = 0`
- `cancelled_count = 0`

**Result**
- Status: `PASSED`
- Notes: Returned `run_status=COMPLETED`, `remitted_count=1`, `failed_count=0`, `cancelled_count=0`.

---

## Test Case 2: Idempotency (Same Key, Same Period)

**Constraints covered**
- idempotency
- no duplicate payout creation

**Setup**
- Reuse dataset from Test Case 1.

**Request**
1. Call `POST /generate-remittances-for-all-users` with:
   - same period
   - same `idempotency_key: tc1_run_001`
2. Call it again with the same payload.

**Expected**
- Same `run_id` returned for repeated call.
- No duplicate remittance lines for the same run key.

**Result**
- Status: `PASSED`
- Notes: Repeated calls returned same `run_id=1`; DB check confirmed `remittance` count for key `tc1_run_001` is `1`.

---

## Test Case 3: Work Evolves After Payment (Additional Segment)

**Constraints covered**
- work can evolve after payment
- immutable history
- financial correctness over time

**Setup**
1. Run successful settlement for period January.
2. Add additional `worklog_entry` on same worklog in January (for example `+20.00`) after first settlement.

**Request**
- Run settlement again for same January period with new key:
  - `idempotency_key: tc3_run_002`
  - `X-Payout-Mode: success`

**Expected**
- New remittance includes only newly unpaid delta (not original paid amount).
- Previous successful lines remain unchanged.

**Result**
- Status: `PASSED`
- Notes: After adding `+20.00`, rerun (`tc3_run_002`) remitted only delta amount `20.00`.

---

## Test Case 4: Retroactive Adjustment (Negative) On Already Settled Work

**Constraints covered**
- retroactive adjustments
- negative balances
- immutable history

**Setup**
1. Have a previously remitted worklog in January.
2. Add adjustment entry in January: `-50.00`.

**Request**
- Run January settlement with new key:
  - `idempotency_key: tc4_run_003`
  - `X-Payout-Mode: success`

**Expected**
- If net user total in period is non-positive, remittance result is `SKIPPED_NEGATIVE`.
- No payout is issued for negative total.

**Result**
- Status: `PASSED`
- Notes: After `-50.00` adjustment, rerun returned `SKIPPED_NEGATIVE` with amount `-50.00`; no payout issued.

---

## Test Case 5: Simulated Failure Path

**Constraints covered**
- settlement attempts may fail
- failed remittance remains unpaid and can be retried in future run

**Setup**
- One unpaid positive worklog amount exists in chosen period.

**Request**
- `POST /generate-remittances-for-all-users`
- Same period
- `idempotency_key: tc5_run_fail_001`
- Header: `X-Payout-Mode: fail`

**Expected**
- User remittance status `FAILED`
- Run status reflects failure (`PARTIAL_SUCCESS` or equivalent when mixed)
- Amount is still considered unpaid for later successful run

**Result**
- Status: `PASSED`
- Notes: Failure simulation returned user result `FAILED` and run status `PARTIAL_SUCCESS`; outstanding remained for future retry.

---

## Test Case 6: Simulated Cancel Path

**Constraints covered**
- settlement attempts may be cancelled

**Setup**
- One unpaid positive worklog amount exists.

**Request**
- `POST /generate-remittances-for-all-users`
- `idempotency_key: tc6_run_cancel_001`
- Header: `X-Payout-Mode: cancel`

**Expected**
- User remittance status `CANCELLED`
- No successful remittance lines created for this attempt

**Result**
- Status: `PASSED`
- Notes: Cancel simulation returned user result `CANCELLED`; DB check confirmed zero `remittance_line` rows for this run key.

---

## Test Case 7: Failure Then Recovery In Next Run (Combined)

**Constraints covered**
- failure handling
- retry via future run
- idempotency per run key
- financial correctness over time

**Setup**
1. Create unpaid positive amount in period.
2. Run with `X-Payout-Mode: fail`.

**Request**
1. Failed run:
   - `idempotency_key: tc7_run_fail_001`
   - `X-Payout-Mode: fail`
2. Recovery run:
   - new key `idempotency_key: tc7_run_success_002`
   - `X-Payout-Mode: success`

**Expected**
- First run stores `FAILED`.
- Second run remits the same still-unpaid amount successfully.
- No double payment after success.

**Result**
- Status: `PASSED`
- Notes: Fail run stored `FAILED`; next success run remitted outstanding `70.00` once, with no over-remittance.

---

## Test Case 8: Strict Period Exclusion (Out-of-Window Entries)

**Constraints covered**
- strict period payout only

**Setup**
- Add two entries on same worklog:
  - `+20.00` within January
  - `+30.00` in February

**Request**
- Settle January only:
  - `from_date: 2026-01-01`
  - `to_date: 2026-01-31`
  - `idempotency_key: tc8_run_001`
  - `X-Payout-Mode: success`

**Expected**
- January run includes only `20.00`.
- February entry is excluded from this run.

**Result**
- Status: `PASSED`
- Notes: January-only settlement remitted `20.00`; February `+30.00` was excluded from the January run.

---

## Test Case 9: List Worklogs Filter Validation

**Constraints covered**
- `/list-all-worklogs` filtering
- amount visibility per worklog

**Request**
1. `GET /list-all-worklogs?remittanceStatus=REMITTED`
2. `GET /list-all-worklogs?remittanceStatus=UNREMITTED`
3. `GET /list-all-worklogs?remittanceStatus=BAD_VALUE`

**Expected**
- `REMITTED` and `UNREMITTED` return filtered lists and amounts.
- invalid value returns `400`.

**Result**
- Status: `PASSED`
- Notes: `REMITTED` and `UNREMITTED` filters returned correct lists; invalid filter returned HTTP `400`.

---

## Test Case 10: Additional Segment + Retroactive Adjustment In Sequence (Combined)

**Constraints covered**
- work evolves after payment
- retroactive adjustment
- strict period correctness
- immutable history / delta remittance behavior

**Setup**
1. Use period January (`2026-01-01` to `2026-01-31`).
2. Initial state for one worklog:
   - Entry A: `+100.00` in January.
3. Run settlement once with:
   - `idempotency_key: tc10_run_initial_001`
   - `X-Payout-Mode: success`
4. After initial payment, append two new entries (same worklog, same period), one after another:
   - Entry B (additional segment): `+30.00`
   - Entry C (adjustment): `-20.00`

**Request**
- Run settlement again for January with new key:
  - `idempotency_key: tc10_run_delta_002`
  - `X-Payout-Mode: success`

**Expected**
- Second run should settle only net delta `+10.00` (`+30 - 20`), not replay old `+100.00`.
- Financial check after second run:
  - period gross = `110.00`
  - period remitted = `110.00`
  - period remaining = `0.00`

**Result**
- Status: `PASSED`
- Notes: Delta run remitted `10.00`; post-run worklog showed `gross=110.00`, `remitted=110.00`, `remaining=0.00`.

---

## Test Case 11: Previous Failed Remittance Succeeds In Next Run (Explicit)

**Constraints covered**
- failed settlement attempts
- next-run recovery
- correctness over time without double payment

**Setup**
1. Period January with one unpaid entry `+75.00`.

**Request**
1. First run (force failure):
   - `idempotency_key: tc11_run_fail_001`
   - `X-Payout-Mode: fail`
2. Second run (new key, success):
   - `idempotency_key: tc11_run_success_002`
   - `X-Payout-Mode: success`

**Expected**
- First run result includes `FAILED` and does not mark the amount as remitted.
- Second run remits the same outstanding `75.00`.
- Combined remitted amount should be exactly `75.00` (no double payment).

**Result**
- Status: `PASSED`
- Notes: First run `FAILED`, second run remitted `75.00`; successful remittance total verified as exactly `75.00`.

---

## Final Execution Summary

- Total cases: `11`
- Passed: `11`
- Failed: `0`
- Pending: `0`

### Case-by-case tracker

1. Basic Strict Period Remittance (Success): `PASSED`
2. Idempotency (Same Key, Same Period): `PASSED`
3. Work Evolves After Payment: `PASSED`
4. Retroactive Adjustment (Negative): `PASSED`
5. Simulated Failure Path: `PASSED`
6. Simulated Cancel Path: `PASSED`
7. Failure Then Recovery In Next Run: `PASSED`
8. Strict Period Exclusion: `PASSED`
9. List Worklogs Filter Validation: `PASSED`
10. Additional Segment + Retroactive Adjustment In Sequence: `PASSED`
11. Previous Failed Remittance Succeeds In Next Run: `PASSED`
