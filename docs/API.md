# WorkLog Payment Dashboard – API Documentation

This document describes the API for the WorkLog Payment Dashboard: worklogs, payments, and authentication used by the solution.

**Interactive docs (when the backend is running):**

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

Base URL for all API v1 endpoints: `http://localhost:8000/api/v1`

---

## Authentication

All worklogs and payments endpoints require a valid JWT. Send it in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Obtain a token

**POST** `/api/v1/login/access-token`

- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:** `username` (email), `password`
- **Response:** `{ "access_token": "...", "token_type": "bearer" }`

Example with `curl`:

```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=yourpassword"
```

### Test token

**POST** `/api/v1/login/test-token`

- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** Current user object

---

## Worklogs

Worklogs represent work done by freelancers on tasks. Each worklog has one or more time entries; the API returns the total amount earned per worklog.

### List worklogs

**GET** `/api/v1/worklogs/`

Returns a paginated list of worklogs with optional filters.

| Query parameter    | Type   | Required | Description |
|-------------------|--------|----------|-------------|
| `skip`            | int    | No       | Offset (default: 0) |
| `limit`           | int    | No       | Max results (default: 100, max: 500) |
| `date_from`       | string | No       | Filter by time entry date (YYYY-MM-DD) |
| `date_to`         | string | No       | Filter by time entry date (YYYY-MM-DD) |
| `remittance_status` | string | No    | `REMITTED` or `UNREMITTED` |

**Response:** `WorkLogsPublic`

```json
{
  "data": [
    {
      "id": "uuid",
      "task_id": "uuid",
      "task_title": "API development",
      "user_id": "uuid",
      "user_email": "freelancer@example.com",
      "user_full_name": "Jane Doe",
      "amount_cents": 42000,
      "remittance_id": "uuid-or-null",
      "remittance_status": "PENDING-or-null"
    }
  ],
  "count": 42
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/worklogs/?skip=0&limit=100&remittance_status=UNREMITTED" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get worklog by ID

**GET** `/api/v1/worklogs/{work_log_id}`

Returns a single worklog with its time entries.

**Response:** `WorkLogDetail` (extends worklog item with `time_entries`)

```json
{
  "id": "uuid",
  "task_id": "uuid",
  "task_title": "API development",
  "user_id": "uuid",
  "user_email": "freelancer@example.com",
  "user_full_name": "Jane Doe",
  "amount_cents": 42000,
  "remittance_id": null,
  "remittance_status": null,
  "time_entries": [
    {
      "id": "uuid",
      "work_log_id": "uuid",
      "entry_date": "2025-01-15",
      "duration_minutes": 120,
      "amount_cents": 24000,
      "description": "Initial implementation"
    }
  ]
}
```

---

## Payments

Payments are done in two steps: **preview** (see eligible worklogs in a date range) and **confirm** (create remittances for the selected worklogs).

### Preview payment batch

**GET** `/api/v1/payments/preview`

Returns worklogs that are eligible for payment in the given date range (unremitted only). Use this to review what will be paid before confirming.

| Query parameter | Type   | Required | Description |
|----------------|--------|----------|-------------|
| `date_from`   | string | Yes      | Period start (YYYY-MM-DD) |
| `date_to`     | string | Yes      | Period end (YYYY-MM-DD) |

**Response:** `PaymentBatchPreview`

```json
{
  "work_logs": [ /* same shape as WorkLogListItem */ ],
  "total_amount_cents": 84000,
  "period_start": "2025-01-01",
  "period_end": "2025-01-31"
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/payments/preview?date_from=2025-01-01&date_to=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Confirm payment

**POST** `/api/v1/payments/confirm`

Creates remittances for the selected worklogs. One remittance per freelancer; worklogs not in `include_work_log_ids` are ignored; freelancers in `exclude_freelancer_ids` are skipped.

**Request body:** `ConfirmPaymentRequest`

```json
{
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "include_work_log_ids": ["uuid1", "uuid2"],
  "exclude_freelancer_ids": ["user-uuid-to-skip"]
}
```

**Response:** List of `RemittancePublic`

```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "status": "PENDING",
    "total_amount_cents": 42000
  }
]
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/payments/confirm" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"period_start":"2025-01-01","period_end":"2025-01-31","include_work_log_ids":["wl-uuid-1","wl-uuid-2"],"exclude_freelancer_ids":[]}'
```

---

## Data types

| Type / field           | Description |
|-----------------------|-------------|
| `amount_cents`        | Amount in cents (e.g. 24000 = $240.00) |
| `remittance_status`   | `PENDING`, `COMPLETED`, `FAILED`, `CANCELLED` or null if not yet remitted |
| `remittance_id`       | Set when the worklog is included in a payment batch |
| `WorkLogRemittanceFilter` | Query filter: `REMITTED` (paid) or `UNREMITTED` (unpaid) |

---

## Users (relevant to the solution)

- **GET** `/api/v1/users/me` – Current user (requires auth).
- **POST** `/api/v1/users/signup` – Register (no auth).
- **GET** `/api/v1/users/` – List users (requires auth).

For full user and auth endpoints, see [http://localhost:8000/docs](http://localhost:8000/docs).
