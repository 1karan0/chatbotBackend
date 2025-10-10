from datetime import timedelta
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Tenant
from auth.jwt_handler import jwt_handler
from services.data_loader import data_loader
from config.settings import settings

from models.schemas import TokenResponse, TenantInfo, UserInfo

router = APIRouter(prefix="/auth", tags=["authentication"])


# ---------------- LOGIN (Swagger-compatible) ----------------
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),  # form-data from Swagger
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    username = form_data.username
    password = form_data.password

    user = db.query(User).filter(User.username == username).first()
    
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
    """Create a new tenant and admin user."""
    tenant_id = tenant_data.get("tenant_id")
    tenant_name = tenant_data.get("tenant_name")
    username = tenant_data.get("username")
    
    if not tenant_id or not tenant_name or not username :
        raise HTTPException(
            status_code=400,
            detail="tenant_id, tenant_name, username are required"
        )
    
    if db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first():
        raise HTTPException(status_code=400, detail="Tenant ID already exists")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    try:
        tenant = Tenant(tenant_id=tenant_id, tenant_name=tenant_name)
        db.add(tenant)
        db.flush()
        
        # hashed_password = jwt_handler.hash_password(password)
        user = User(username=username, tenant_id=tenant.tenant_id)
        db.add(user)
        
        data_loader.create_tenant_directory(tenant_id)
        
        db.commit()
        return user
        
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
    
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    try:
        hashed_password = jwt_handler.hash_password(password)
        user = User(username=username, hashed_password=password, tenant_id=tenant_id)
        db.add(user)
        db.commit()
        
        return {"message": "User created successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


# ---------------- GET TENANTS ----------------
@router.get("/tenants", response_model=List[TenantInfo])
async def get_all_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).all()


@router.get("/tenants/{tenant_id}", response_model=TenantInfo)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

# ---------------- DELETE TENANT ----------------
@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
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
    return db.query(User).all()


@router.get("/users/{user_id}", response_model=UserInfo)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/tenants/{tenant_id}/users", response_model=List[UserInfo])
async def get_tenant_users(tenant_id: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.tenant_id == tenant_id).all()
