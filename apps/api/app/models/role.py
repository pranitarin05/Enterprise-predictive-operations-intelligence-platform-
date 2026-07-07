"""
Role model — defines a named permission set (viewer, analyst, ml_engineer, admin).
Permissions are stored as JSONB so we can add new permission keys later
without another schema migration for every new permission.
"""

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"
