from database.connection import SessionLocal
from database.models import User, Tenant  # Import your models

def check_all_data():
    db = SessionLocal()
    try:
        print("=== CHECKING DATABASE CONTENTS ===")
        
        # Check Tenants
        tenants = db.query(Tenant).all()
        print(f"\n📊 TENANTS ({len(tenants)} found):")
        for tenant in tenants:
            print(f"  ID: {tenant.tenant_id}")
            print(f"  Name: {tenant.tenant_name}")
            print(f"  Created: {tenant.created_at}")
            print(f"  Active: {tenant.is_active}")
            print("  " + "-" * 30)
        
        # Check Users
        users = db.query(User).all()
        print(f"\n👥 USERS ({len(users)} found):")
        for user in users:
            print(f"  ID: {user.user_id}")
            print(f"  Username: {user.username}")
            print(f"  Tenant ID: {user.tenant_id}")
            print(f"  Active: {user.is_active}")
            print(f"  Created: {user.created_at}")
            print("  " + "-" * 30)
            
        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"  Total Tenants: {len(tenants)}")
        print(f"  Total Users: {len(users)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_all_data()