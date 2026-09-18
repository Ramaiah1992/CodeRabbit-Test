from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class User:
    id: int
    email: str
    created_at: str

    @classmethod
    def from_row(cls, row):
        return cls(id=row["id"], email=row["email"], created_at=row["created_at"])

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Task:
    id: int
    user_id: int
    title: str
    description: str
    status: str
    priority: int
    due_date: Optional[str]
    created_at: str

    VALID_STATUSES = ("open", "in_progress", "done")
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            due_date=row["due_date"],
            created_at=row["created_at"],
        )

    def to_dict(self):
        return asdict(self)
