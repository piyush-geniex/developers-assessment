# FastAPI Best Practices for AI Agents

This document provides guidelines for AI agents working on FastAPI projects. Follow these conventions when writing or modifying code.

## Project Structure

Organize code by domain, not by file type. Domain here implies a very broad grouping of business logic. 
For example, for Financial domain, all tables and services related to this should be under 1 single folder.

```
src/
├── {domain}/           # e.g., auth/, posts/, aws/
│   ├── router.py       # API endpoints
│   ├── schemas.py      # Pydantic models
│   ├── models.py       # Database models
│   ├── service.py      # Business logic
│   ├── dependencies.py # Route dependencies
│   ├── config.py       # Environment variables
│   ├── constants.py    # Constants and error codes
│   ├── exceptions.py   # Domain-specific exceptions
│   └── utils.py        # Helper functions
├── config.py           # Global configuration
├── models.py           # Global models
├── exceptions.py       # Global exceptions
├── database.py         # Database connection
└── main.py             # FastAPI app initialization
```

**Import Convention**: Use explicit module names when importing across domains:
```python
from src.auth import constants as auth_constants
from src.notifications import service as notification_service
```

## Async 

### Rules
- `async def` routes: Use ONLY non-blocking I/O (`await` calls)
- `def` routes (sync): Use for blocking I/O (runs in threadpool automatically)
- Do not use async functions anywhere unless explicitly told to.

### Common Mistakes to Avoid
```python
# WRONG: Blocking call in async route
@router.get("/bad")
async def bad_route():
    time.sleep(10)  # Blocks entire event loop
    return {"status": "done"}

# CORRECT: Non-blocking in async route
@router.get("/good")
async def good_route():
    await asyncio.sleep(10)
    return {"status": "done"}

# CORRECT: Sync route for blocking operations
@router.get("/also-good")
def sync_route():
    time.sleep(10)  # Runs in threadpool
    return {"status": "done"}
```



## Pydantic

### Use Built-in Validators only when asked
```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128, pattern="^[A-Za-z0-9-_]+$")
    email: EmailStr
    age: int = Field(ge=18)
```

### By default, always generate custom validators for every field in a model. Example:

```python
class UserCreate(BaseModel):
    username: str
    email: str
    age: int
    signup_date: date

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if value is None:
            raise ValueError("username is required")

        if not isinstance(value, str):
            raise ValueError("username must be a string")

        value = value.strip()

        if len(value) == 0:
            raise ValueError("username cannot be empty")

        if len(value) > 128:
            raise ValueError("username too long")

        if not re.match(r"^[A-Za-z0-9_-]+$", value):
            raise ValueError("username contains invalid characters")

        return value
```

### Custom Base Model
Create a shared base model for consistent serialization:
```python
from pydantic import BaseModel, ConfigDict

class CustomModel(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: datetime_to_gmt_str},
        populate_by_name=True,
    )
```


## Database

### Naming Conventions
- Use `lower_case_snake` format
- Singular table names: `post`, `user`, `post_like`


###Schema design and data modelling
-  Never create many-to-many relationships between tables unless explicitly asked.
- To simplify data access and reduce join complexity, prefer storing related data in a single table rather than spreading logic across multiple normalized tables.


###Business Logic Placement

Keep logic close to where it is used to reduce indirection.

@router.post("/users")
async def create_user(payload: UserCreate):
    if payload.age < 18:
        raise HTTPException(status_code=400, detail="Too young")

    user = User(**payload.dict())
    db.add(user)
    db.commit()
    return user


Services are optional and should be introduced only when logic is reused across multiple endpoints.


### Exception handling

Raise HTTPException Directly From Service and Utility Layers


To reduce boilerplate and avoid unnecessary translation layers, services and helper functions may raise HTTPException directly instead of defining domain-specific exceptions.

from fastapi import HTTPException, status

def create_user(data: dict):
    if not data.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )

    if user_exists(data["email"]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    return save_user(data)

### Queries Approach
Prefer database-level operations only when explicitly asked:
- Complex joins
- Data aggregation
- Building nested JSON responses

By default, prefer encoding complex business logic operations using python, instead of DB queries.

## Migrations (Alembic)

- Keep migrations static and reversible
- Use descriptive file names: `2022-08-24_post_content_idx.py`
- Configure in alembic.ini:
  ```ini
  file_template = %%(year)d-%%(month).2d-%%(day).2d_%%(slug)s
  ```


## Testing

Use async test client from the start. Tests should not test any business logic, instead, should just test if interfaces are correct, unless explicitly overidden:
```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.mark.asyncio
async def test_endpoint(client: AsyncClient):
    resp = await client.post("/posts")
    assert resp.status_code == 201
```

## Linting

Use ruff for formatting and linting:
```shell
ruff check --fix src
ruff format src
```
