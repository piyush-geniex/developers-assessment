# Fullstack Assessment: WorkLog Payment Dashboard

## Background

You're building an admin dashboard for a company that hires freelancers. Freelancers log their time against tasks, and at the end of each payment cycle, an admin reviews the logged work and processes payments. Each task has a worklog that contains multiple time entries recorded by the freelancer. The admin needs to see what work was done, decide what to pay for, and issue payments.

---

## Requirements

1. User wants to see a list of all worklogs and how much was earned per task
2. User wants to drill down into a worklog to see individual time entries
3. User wants to select a date range to filter worklogs eligible for payment
4. User wants to review the selection before confirming payment
5. User wants to exclude specific worklogs or freelancers from a payment batch

---

## Setup Instructions

To start development, simply run:

```bash
docker compose up db backend frontend
```

This will start all required services including the backend API, frontend, database, and any other dependencies. Once the services are up, you can access:

- **Frontend:** `http://localhost:5173`
- **API Documentation:** `http://localhost:8000/docs`
- **Backend API:** `http://localhost:8000`

---

## Required Documentation

Your implementation must include:

a. **Screenshots**
   - Include screenshots of all screens you think are relevant to your implementation.
   - This helps reviewers understand your UI/UX decisions and workflow.
   - Save them in a `screenshots/` folder or include them in your PR description.

### Submission Checklist

- [ ] Working backend APIs implementing the required functionality
- [ ] Functional frontend implementing the workflows above
- [ ] Added screenshots of relevant screens
- [ ] Created Pull Request

---

## Technology Stack

This project uses:

- **FastAPI** - Python backend framework
- **SQLModel** - SQL database ORM
- **PostgreSQL** - Database
- **Next.js** - React frontend framework
- **Docker Compose** - Container orchestration



