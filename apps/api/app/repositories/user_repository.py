"""
User repository -- the ONLY place allowed to query the users table.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    tenant_id: uuid.UUID,
    role_id: uuid.UUID,
    email: str,
    hashed_password: str,
) -> User:
    user = User(
        tenant_id=tenant_id,
        role_id=role_id,
        email=email,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
