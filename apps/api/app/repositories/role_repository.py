"""
Role repository -- the ONLY place allowed to query the roles table.
"""

from sqlalchemy.orm import Session

from app.models.role import Role


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.query(Role).filter(Role.name == name).first()


def create_role(db: Session, name: str, permissions: dict) -> Role:
    role = Role(name=name, permissions=permissions)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role
