"""
Tenant repository -- the ONLY place allowed to query the tenants table.
Routes and services never write raw SQLAlchemy queries directly; they
call functions here instead. This keeps data access logic in one place,
testable and swappable independent of business logic.
"""

from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def get_tenant_by_name(db: Session, name: str) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.name == name).first()


def create_tenant(db: Session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)  # loads DB-generated fields like id, created_at
    return tenant
