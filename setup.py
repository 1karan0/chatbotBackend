#!/usr/bin/env python3
"""
Setup script for Multi-Tenant RAG Chatbot
"""

import os
import sys
import sqlite3
from pathlib import Path

def create_directory_structure():
    """Create necessary directories."""
    directories = [
        "data/tenant_a",
        "data/tenant_b", 
        "data/tenant_c",
        "data/tenant_d",
        "data/tenant_e",
        "data/tenant_all",
        "chroma_db",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_sample_data():
    """Create sample data files for demonstration."""
    sample_data = {
        "data/tenant_a/london.txt": "London office services:\nWe provide software development, consulting, and support services in London.\nOur London team specializes in web applications and mobile development.\nContact: london@company.com",
        
        "data/tenant_b/manchester.txt": "Manchester office services:\nWe offer cloud solutions, DevOps, and infrastructure management in Manchester.\nOur Manchester team focuses on scalable cloud architectures.\nContact: manchester@company.com",
        
        "data/tenant_c/birmingham.txt": "Birmingham office services:\nWe provide data analytics, machine learning, and AI solutions in Birmingham.\nOur Birmingham team specializes in data science and artificial intelligence.\nContact: birmingham@company.com",
        
        "data/tenant_d/glasgow.txt": "Glasgow office services:\nWe offer cybersecurity, network solutions, and IT support in Glasgow.\nOur Glasgow team focuses on security and infrastructure.\nContact: glasgow@company.com",
        
        "data/tenant_e/midlands.txt": "Midlands office services:\nWe provide business consulting, project management, and training in the Midlands.\nOur Midlands team specializes in business transformation.\nContact: midlands@company.com",
        
        "data/tenant_all/all-services.txt": "Company-wide services:\nWe offer 24/7 customer support across all locations.\nGeneral inquiries: info@company.com\nFor specific location services, please contact your local office.\nEmergency support: +44-800-123-4567"
    }
    
    for file_path, content in sample_data.items():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created sample data: {file_path}")

def create_env_file():
    """Create .env file if it doesn't exist."""
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("""# Multi-Tenant RAG Chatbot Configuration

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# JWT Configuration  
SECRET_KEY=super-secret-jwt-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Database Configuration
DATABASE_URL=sqlite:///./app.db

# Storage Configuration
CHROMA_PATH=./chroma_db
DATA_PATH=./data

# External Services
NGROK_AUTH_TOKEN=326XQY64T2IlwvoXxgWZZgCURGR_3Dzi2gaTewvfUasE3NWiH
""")
        print("Created .env file - please update with your actual API keys!")
    else:
        print(".env file already exists")

def initialize_database():
    """Initialize SQLite database with sample data."""
    from database.connection import create_tables, get_db
    from database.models import Tenant, User
    from auth.jwt_handler import jwt_handler
    
    # Create tables
    create_tables()
    print("Database tables created")
    
    # Add sample tenants and users
    db = next(get_db())
    
    sample_tenants = [
        {"tenant_id": "tenant_a", "tenant_name": "London Office"},
        {"tenant_id": "tenant_b", "tenant_name": "Manchester Office"},
        {"tenant_id": "tenant_c", "tenant_name": "Birmingham Office"},
        {"tenant_id": "tenant_d", "tenant_name": "Glasgow Office"},
        {"tenant_id": "tenant_e", "tenant_name": "Midlands Office"},
    ]
    
    sample_users = [
        {"username": "london_user", "password": "london123", "tenant_id": "tenant_a"},
        {"username": "manchester_user", "password": "manchester123", "tenant_id": "tenant_b"},
        {"username": "birmingham_user", "password": "birmingham123", "tenant_id": "tenant_c"},
        {"username": "glasgow_user", "password": "glasgow123", "tenant_id": "tenant_d"},
        {"username": "midlands_user", "password": "midlands123", "tenant_id": "tenant_e"},
    ]
    
    try:
        # Add tenants
        for tenant_data in sample_tenants:
            existing_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_data["tenant_id"]).first()
            if not existing_tenant:
                tenant = Tenant(**tenant_data)
                db.add(tenant)
        
        # Add users
        for user_data in sample_users:
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing_user:
                hashed_password = jwt_handler.hash_password(user_data["password"])
                user = User(
                    username=user_data["username"],
                    hashed_password=hashed_password,
                    tenant_id=user_data["tenant_id"]
                )
                db.add(user)
        
        db.commit()
        print("Sample tenants and users created")
        
        # Display sample credentials
        print("\n" + "="*50)
        print("SAMPLE LOGIN CREDENTIALS:")
        print("="*50)
        for user in sample_users:
            print(f"Tenant: {user['tenant_id']} | Username: {user['username']} | Password: {user['password']}")
        print("="*50)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating sample data: {e}")
    finally:
        db.close()

def main():
    """Main setup function."""
    print("Setting up Multi-Tenant RAG Chatbot...")
    print("="*50)
    
    # Create directory structure
    create_directory_structure()
    print()
    
    # Create .env file
    create_env_file()
    print()
    
    # Create sample data files
    create_sample_data()
    print()
    
    # Initialize database
    initialize_database()
    print()
    
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Update the .env file with your actual OpenAI API key")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the application: python main.py")
    print("4. Or run with ngrok: python run_with_ngrok.py")
    print("5. Access the API docs at http://localhost:8000/docs")

if __name__ == "__main__":
    main()