from datetime import timedelta
from typing import List, Dict, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Users, Tenants
from auth.jwt_handler import jwt_handler
from services.data_loader import data_loader
from config.settings import settings

from models.schemas import TokenResponse, TenantInfo, UserInfo, TenantUserInfo

router = APIRouter(prefix="/auth", tags=["authentication"])


def _serialize_user(user: Users) -> UserInfo:
    """Map current DB user shape to API user response model."""
    user_id = user.id if isinstance(user.id, UUID) else UUID(str(user.id))
    tenant_id = user.tenantsTenant_id if isinstance(user.tenantsTenant_id, UUID) else (
        UUID(str(user.tenantsTenant_id)) if user.tenantsTenant_id else None
    )

    return UserInfo(
        user_id=user_id,
        username=user.name or user.email,
        tenant_id=tenant_id,
        tenant_ids=[tenant_id] if tenant_id else [],
        is_active=True,
        created_at=user.createdAt
    )


def _serialize_tenant(tenant: Tenants, db: Session) -> TenantInfo:
    """Map tenant row to API response with linked user_id."""
    linked_user: Optional[Users] = (
        db.query(Users)
        .filter(Users.tenantsTenant_id == tenant.tenant_id)
        .order_by(Users.createdAt.asc())
        .first()
    )
    user_id: Optional[UUID] = None
    if linked_user is not None:
        uid = linked_user.id
        user_id = uid if isinstance(uid, UUID) else UUID(str(uid))

    return TenantInfo(
        tenant_id=tenant.tenant_id,
        tenant_name=tenant.tenant_name,
        created_at=tenant.created_at,
        user_id=user_id,
        user=_serialize_user(linked_user) if linked_user else None
    )


# ---------------- LOGIN (Swagger-compatible) ----------------
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),  # form-data from Swagger
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    username = form_data.username
    password = form_data.password

    user = db.query(Users).filter(Users.username == username).first()
    
    if not user or not jwt_handler.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = jwt_handler.create_access_token(
        data={"sub": user.user_id, "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


# ---------------- CREATE TENANT ----------------
@router.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: Dict[str, str],  # accept JSON dictionary
    db: Session = Depends(get_db)
):
    """Create a new tenant."""
    tenant_id = tenant_data.get("tenant_id")
    tenant_name = tenant_data.get("tenant_name")
    user_id = tenant_data.get("user_id")
    
    if not tenant_id or not tenant_name or not user_id:
        raise HTTPException(
            status_code=400,
            detail="tenant_id, tenant_name, and user_id are required"
        )
    
    if db.query(Tenants).filter(Tenants.tenant_id == tenant_id).first():
        raise HTTPException(status_code=400, detail="Tenant ID already exists")
    
    try:
        linked_user = db.query(Users).filter(Users.id == user_id).first()
        if not linked_user:
            raise HTTPException(status_code=404, detail="User not found")

        tenant = Tenants(tenant_id=tenant_id, tenant_name=tenant_name)
        db.add(tenant)
        db.flush()

        linked_user.tenantsTenant_id = tenant.tenant_id
        
        data_loader.create_tenant_directory(tenant_id)
        
        db.commit()
        return {
            "message": "Tenant created successfully",
            "tenant_id": str(tenant.tenant_id),
            "tenant_name": tenant.tenant_name,
            "user_id": str(user_id),
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating tenant: {str(e)}")


# ---------------- CREATE USER ----------------
@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: Dict[str, str],  # accept JSON dictionary
    db: Session = Depends(get_db)
):
    """Create a new user for an existing tenant."""
    tenant_id = user_data.get("tenant_id")
    username = user_data.get("username")
    password = user_data.get("password")
    
    if not tenant_id or not username :
        raise HTTPException(
            status_code=400,
            detail="tenant_id, username, and password are required"
        )
    
    tenant = db.query(Tenants).filter(Tenants.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if db.query(Users).filter(Users.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    try:
        hashed_password = jwt_handler.hash_password(password)
        user = Users(username=username, hashed_password=password, tenant_id=tenant_id)
        db.add(user)
        db.commit()
        
        return {"message": "User created successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


# ---------------- GET TENANTS ----------------
@router.get("/tenants", response_model=List[TenantInfo])
async def get_all_tenants(db: Session = Depends(get_db)):
    tenants = db.query(Tenants).all()
    return [_serialize_tenant(tenant, db) for tenant in tenants]


@router.get("/tenants/{tenant_id}", response_model=TenantInfo)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenants).filter(Tenants.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return _serialize_tenant(tenant, db)

# ---------------- DELETE TENANT ----------------
@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenants).filter(Tenants.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    try:
        db.delete(tenant)
        db.commit()
        return HTTPException(status_code=204, detail="Tenant deleted successfully") 
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting tenant: {str(e)}")
    
# ---------------- GET USERS ----------------
@router.get("/users", response_model=List[UserInfo])
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return [_serialize_user(user) for user in users]

 
@router.get("/users/{user_id}", response_model=UserInfo)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user(user)


@router.get("/tenants/{tenant_id}/users", response_model=List[UserInfo])
async def get_tenant_users(tenant_id: str, db: Session = Depends(get_db)):
    users = db.query(Users).filter(Users.tenantsTenant_id == tenant_id).all()
    return [_serialize_user(user) for user in users]
