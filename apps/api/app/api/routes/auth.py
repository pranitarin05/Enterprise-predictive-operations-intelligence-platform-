"""
Auth routes -- thin HTTP layer. Only translates between HTTP and the
service layer; no business logic lives here.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
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
