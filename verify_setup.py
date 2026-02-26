"""
Verify that the application setup is correct.
This script checks:
1. PostgreSQL connection
2. ChromaDB initialization
3. Environment variables
"""
import os
import sys
from dotenv import load_dotenv

# Fix SQLite for ChromaDB
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("✓ SQLite module configured for ChromaDB")
except ImportError:
    print("⚠ pysqlite3 not available, using default sqlite3")

load_dotenv()

def check_env_vars():
    """Check required environment variables."""
    print("\n=== Checking Environment Variables ===")
    required_vars = [
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'PG_USER',
        'PG_DB',
        'PG_PASSWORD',
        'PG_PORT',
        'CHROMA_PATH',
        'DATA_PATH'
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: NOT SET")
            missing.append(var)

    return len(missing) == 0

def check_postgresql():
    """Check PostgreSQL connection."""
    print("\n=== Checking PostgreSQL Connection ===")
    try:
        from sqlalchemy import create_engine, text
        from config.settings import settings

        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL connected successfully")
            print(f"  Version: {version[:50]}...")
            return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False

def check_chromadb():
    """Check ChromaDB initialization."""
    print("\n=== Checking ChromaDB ===")
    try:
        from config.settings import settings
        from langchain_community.vectorstores import Chroma
        from langchain_openai import OpenAIEmbeddings

        chroma_path = settings.chroma_path
        print(f"  ChromaDB path: {chroma_path}")

        if os.path.exists(chroma_path):
            print(f"✓ ChromaDB directory exists")
            embeddings = OpenAIEmbeddings(model=settings.embedding_model)
            db = Chroma(
                persist_directory=chroma_path,
                embedding_function=embeddings
            )
            print(f"✓ ChromaDB initialized successfully")
            return True
        else:
            print(f"⚠ ChromaDB directory does not exist (will be created on first use)")
            return True
    except Exception as e:
        print(f"✗ ChromaDB initialization failed: {e}")
        return False

def check_data_directory():
    """Check data directory."""
    print("\n=== Checking Data Directory ===")
    try:
        from config.settings import settings
        data_path = settings.data_path

        if os.path.exists(data_path):
            print(f"✓ Data directory exists: {data_path}")

            # Count tenant data files
            tenant_dirs = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]
            print(f"  Found {len(tenant_dirs)} tenant directories:")
            for tenant_dir in tenant_dirs:
                files = os.listdir(os.path.join(data_path, tenant_dir))
                print(f"    - {tenant_dir}: {len(files)} files")

            return True
        else:
            print(f"⚠ Data directory does not exist: {data_path}")
            return False
    except Exception as e:
        print(f"✗ Data directory check failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Multi-Tenant RAG Chatbot - Setup Verification")
    print("=" * 60)

    checks = [
        ("Environment Variables", check_env_vars),
        ("PostgreSQL Connection", check_postgresql),
        ("ChromaDB", check_chromadb),
        ("Data Directory", check_data_directory)
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} check failed with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n✓ All checks passed! Your application is ready to run.")
        print("\nTo start the application, run:")
        print("  python main.py")
    else:
        print("\n✗ Some checks failed. Please fix the issues above before running the application.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
