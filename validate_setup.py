#!/usr/bin/env python3
"""
Setup Validation Script
Run this after installation to verify everything is configured correctly
"""

import sys
import os

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.11+")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    required = [
        'fastapi',
        'uvicorn',
        'langchain',
        'langchain_openai',
        'chromadb',
        'sqlalchemy',
        'nltk',
        'beautifulsoup4',
        'pypdf',
        'docx'
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            missing.append(package)

    return len(missing) == 0

def check_nltk_data():
    """Check if NLTK data is downloaded"""
    print("\nChecking NLTK data...")
    try:
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
            print("✅ NLTK punkt data")
        except LookupError:
            print("❌ NLTK punkt data - Not downloaded")
            return False

        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
            print("✅ NLTK averaged_perceptron_tagger data")
        except LookupError:
            print("❌ NLTK averaged_perceptron_tagger data - Not downloaded")
            return False

        return True
    except ImportError:
        print("❌ NLTK not installed")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\nChecking environment configuration...")
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False

    print("✅ .env file exists")

    with open('.env', 'r') as f:
        content = f.read()

    required_vars = [
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'JWT_SECRET_KEY'
    ]

    all_present = True
    for var in required_vars:
        if var in content:
            value = [line.split('=')[1].strip() for line in content.split('\n') if line.startswith(var)]
            if value and value[0] and 'your_' not in value[0].lower():
                print(f"✅ {var} is set")
            else:
                print(f"⚠️  {var} is present but needs to be configured")
                all_present = False
        else:
            print(f"❌ {var} is missing")
            all_present = False

    return all_present

def check_models():
    """Check if database models can be imported"""
    print("\nChecking database models...")
    try:
        from database.models import KnowledgeSource, Tenant, User
        print("✅ Database models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False

def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...")
    dirs = ['data', 'chroma_db']
    all_exist = True

    for directory in dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}/ exists")
        else:
            print(f"⚠️  {directory}/ will be created on first run")

    return True

def main():
    """Run all checks"""
    print("="*50)
    print("Multi-Tenant RAG Chatbot - Setup Validation")
    print("="*50)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_nltk_data(),
        check_env_file(),
        check_directories(),
        check_models()
    ]

    print("\n" + "="*50)
    if all(checks):
        print("✅ All checks passed! Your setup is ready.")
        print("\nTo start the application:")
        print("  python3 main.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nTo fix:")
        print("  1. Run: ./install.sh")
        print("  2. Configure your .env file with proper API keys")
        print("  3. Run this script again to validate")
    print("="*50)

    return all(checks)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
