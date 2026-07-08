"""
Reusable FastAPI dependencies for protecting endpoints.

Any route that adds `current_user: User = Depends(get_current_user)`
now requires a valid JWT and gets the authenticated user injected,
with the database's tenant context already set for RLS.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db_session, set_tenant_context
from app.models.user import User
from app.repositories import user_repository

# tokenUrl is just used to populate FastAPI's /docs "Authorize" button --
# it doesn't affect actual token verification logic below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_error

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if user_id is None or tenant_id is None:
        raise credentials_error

    # Set RLS context BEFORE querying -- this is the enforcement point
    set_tenant_context(db, tenant_id)

    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_error

    return user
