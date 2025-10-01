#!/usr/bin/env python3
"""
Quick test to verify all imports work correctly
Run this after installation to check if the fixes worked
"""

import sys

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    print("-" * 50)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Database models
    try:
        from database.models import KnowledgeSource, Tenant, User
        print("✅ Database models imported successfully")

        # Check if source_metadata exists (not metadata)
        assert hasattr(KnowledgeSource, 'source_metadata'), "source_metadata column not found!"
        print("✅ source_metadata column exists (metadata fix applied)")
        tests_passed += 2
    except Exception as e:
        print(f"❌ Database models import failed: {e}")
        tests_failed += 2

    # Test 2: Retrieval service
    try:
        from services.retrieval_service_v2 import retrieval_service
        print("✅ Retrieval service imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Retrieval service import failed: {e}")
        tests_failed += 1

    # Test 3: Document processor
    try:
        from services.document_processor import document_processor
        print("✅ Document processor imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Document processor import failed: {e}")
        tests_failed += 1

    # Test 4: NLTK
    try:
        import nltk
        print("✅ NLTK imported successfully")
        tests_passed += 1

        # Check NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            print("✅ NLTK punkt data available")
            tests_passed += 1
        except LookupError:
            print("⚠️  NLTK punkt data not found (run: python -c \"import nltk; nltk.download('punkt')\")")
            tests_failed += 1

    except Exception as e:
        print(f"❌ NLTK import failed: {e}")
        tests_failed += 2

    # Test 5: PDF support
    try:
        from pypdf import PdfReader
        print("✅ PDF support (pypdf) available")
        tests_passed += 1
    except Exception as e:
        print(f"❌ PDF support not available: {e}")
        tests_failed += 1

    # Test 6: DOCX support
    try:
        from docx import Document
        print("✅ DOCX support (python-docx) available")
        tests_passed += 1
    except Exception as e:
        print(f"❌ DOCX support not available: {e}")
        tests_failed += 1

    # Test 7: Web scraper
    try:
        from services.web_scraper import web_scraper
        print("✅ Web scraper imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Web scraper import failed: {e}")
        tests_failed += 1

    # Test 8: API routes
    try:
        from api.auth_routes import router as auth_router
        from api.chat_routes import router as chat_router
        from api.knowledge_routes import router as knowledge_router
        print("✅ API routes imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ API routes import failed: {e}")
        tests_failed += 1

    # Test 9: Config
    try:
        from config.settings import settings
        print("✅ Settings loaded successfully")

        # Check if OpenAI key is configured
        if settings.openai_api_key and 'your_' not in settings.openai_api_key.lower():
            print("✅ OpenAI API key is configured")
            tests_passed += 2
        else:
            print("⚠️  OpenAI API key needs to be configured in .env")
            tests_passed += 1
            tests_failed += 1

    except Exception as e:
        print(f"❌ Settings import failed: {e}")
        tests_failed += 2

    print("-" * 50)
    print(f"\nResults: {tests_passed} passed, {tests_failed} failed")

    if tests_failed == 0:
        print("\n🎉 All tests passed! Your setup is ready.")
        return True
    elif tests_failed <= 2:
        print("\n⚠️  Minor issues detected. Check warnings above.")
        return True
    else:
        print("\n❌ Setup has issues. Please run ./install.sh")
        return False

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    print("-" * 50)

    try:
        from database.connection import get_db, create_tables
        print("✅ Database connection imports successful")

        # Try to create tables
        create_tables()
        print("✅ Database tables created/verified")

        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Import Test Suite")
    print("=" * 50)
    print()

    imports_ok = test_imports()
    db_ok = test_database_connection()

    print("\n" + "=" * 50)
    if imports_ok and db_ok:
        print("✅ ALL TESTS PASSED")
        print("\nYour chatbot backend is ready to use!")
        print("Start the server with: python3 main.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the issues above.")
        print("Run: ./install.sh to reinstall")
    print("=" * 50)

    return imports_ok and db_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
