from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# CORRECTED IMPORT - use TenantInfo and UserInfo instead of TenantResponse/UserResponse
from models.schemas import TokenRequest, TokenResponse, TenantCreate, UserCreate, TenantInfo, UserInfo
from database.connection import get_db
from database.models import User, Tenant
from auth.jwt_handler import jwt_handler
from services.data_loader import data_loader
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: TokenRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    # Get user from database
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not jwt_handler.verify_password(form_data.password, user.hashed_password):
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
    
    # Create access token
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

@router.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db)
):
    """Create a new tenant and admin user."""
    # Check if tenant ID already exists
    existing_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_data.tenant_id).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID already exists"
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == tenant_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    try:
        # Create tenant
        tenant = Tenant(
            tenant_id=tenant_data.tenant_id,
            tenant_name=tenant_data.tenant_name
        )
        db.add(tenant)
        db.flush()  # Flush to get the tenant_id
        
        # Create admin user for tenant
        hashed_password = jwt_handler.hash_password(tenant_data.password)
        user = User(
            username=tenant_data.username,
            hashed_password=hashed_password,
            tenant_id=tenant.tenant_id
        )
        db.add(user)
        
        # Create tenant data directory
        data_loader.create_tenant_directory(tenant_data.tenant_id)
        
        db.commit()
        
        return {"message": "Tenant and admin user created successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tenant: {str(e)}"
        )

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user for an existing tenant."""
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.tenant_id == user_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    try:
        # Create user
        hashed_password = jwt_handler.hash_password(user_data.password)
        user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            tenant_id=user_data.tenant_id
        )
        db.add(user)
        db.commit()
        
        return {"message": "User created successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

# CORRECTED GET ENDPOINTS - using TenantInfo and UserInfo
@router.get("/tenants", response_model=List[TenantInfo])
async def get_all_tenants(db: Session = Depends(get_db)):
    """Get all tenants"""
    tenants = db.query(Tenant).all()
    return tenants

@router.get("/tenants/{tenant_id}", response_model=TenantInfo)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Get specific tenant by ID"""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.get("/users", response_model=List[UserInfo])
async def get_all_users(db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}", response_model=UserInfo)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get specific user by ID"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/tenants/{tenant_id}/users", response_model=List[UserInfo])
async def get_tenant_users(tenant_id: str, db: Session = Depends(get_db)):
    """Get all users for a specific tenant"""
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    return users