from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict


def datetime_to_gmt_str(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class CustomModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
