"""
Auth routes -- thin HTTP layer.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories import role_repository
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from app.services.auth_service import register_user, authenticate_user, AuthError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db_session)):
    try:
        user, role = register_user(
            db=db,
            tenant_name=payload.tenant_name,
            email=payload.email,
            password=payload.password,
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return UserResponse(id=user.id, email=user.email, tenant_id=user.tenant_id, role=role.name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)):
    try:
        user, role, access_token, refresh_token = authenticate_user(
            db=db, email=payload.email, password=payload.password
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    The first protected endpoint in the platform. Requires a valid,
    unexpired access token. Proves the full auth chain works end-to-end.
    """
    role = role_repository.get_role_by_name(db, "viewer")  # same known simplification as before
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        tenant_id=current_user.tenant_id,
        role=role.name,
    )
