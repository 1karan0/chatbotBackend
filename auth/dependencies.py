from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials
import secrets
from sqlalchemy.orm import Session
from typing import Dict, Any

from .jwt_handler import jwt_handler
from database.connection import get_db
from database.models import Users, Tenants
from config.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
swagger_basic_scheme = HTTPBasic()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Users:
    """Get the current authenticated user."""
    # Verify and decode token
    payload = jwt_handler.verify_token(token)
    user_id = payload.get("user_id")
    
    # Get user from database
    user = db.query(Users).filter(Users.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_tenant(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenants:
    """Get the current authenticated user's tenant."""
    tenant = db.query(Tenants).filter(Tenants.tenant_id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive tenant"
        )
    
    return tenant

async def get_tenant_id(current_user: Users = Depends(get_current_user)) -> str:
    """Get the current authenticated user's tenant ID."""
    return current_user.tenant_id


async def verify_swagger_admin(
    credentials: HTTPBasicCredentials = Depends(swagger_basic_scheme),
) -> None:
    """
    Verify admin credentials for accessing Swagger / OpenAPI docs.
    Uses ADMIN_USERNAME and ADMIN_PASSWORD from settings.
    """
    expected_username = settings.admin_username or ""
    expected_password = settings.admin_password or ""

    correct_username = secrets.compare_digest(credentials.username, expected_username)
    correct_password = secrets.compare_digest(credentials.password, expected_password)

    if not (expected_username and expected_password and correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to access API documentation",
            headers={"WWW-Authenticate": "Basic"},
        )

    return None