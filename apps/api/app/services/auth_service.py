"""
Auth service -- business logic for registration and login.

This is where the actual "what should happen" rules live: check for
duplicate emails, hash passwords, verify credentials, issue tokens.
Routes call this; this calls repositories. Routes never touch the DB directly.
"""

from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.repositories import tenant_repository, user_repository, role_repository


class AuthError(Exception):
    """Raised for any auth failure the route layer should turn into an HTTP error."""
    pass


DEFAULT_ROLE_NAME = "viewer"
DEFAULT_ROLE_PERMISSIONS = {"can_view_dashboard": True}


def register_user(db: Session, tenant_name: str, email: str, password: str):
    if user_repository.get_user_by_email(db, email):
        raise AuthError("A user with this email already exists.")

    tenant = tenant_repository.get_tenant_by_name(db, tenant_name)
    if tenant is None:
        tenant = tenant_repository.create_tenant(db, tenant_name)

    role = role_repository.get_role_by_name(db, DEFAULT_ROLE_NAME)
    if role is None:
        role = role_repository.create_role(db, DEFAULT_ROLE_NAME, DEFAULT_ROLE_PERMISSIONS)

    new_user = user_repository.create_user(
        db=db,
        tenant_id=tenant.id,
        role_id=role.id,
        email=email,
        hashed_password=hash_password(password),
    )
    return new_user, role


def authenticate_user(db: Session, email: str, password: str):
    user = user_repository.get_user_by_email(db, email)
    if user is None:
        raise AuthError("Invalid email or password.")

    if not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password.")

    role = role_repository.get_role_by_name(db, DEFAULT_ROLE_NAME)  # simple for now
    access_token = create_access_token(
        user_id=str(user.id), tenant_id=str(user.tenant_id), role=role.name
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    return user, role, access_token, refresh_token
