#!/bin/bash

echo "Installing new dependencies for enhanced backend..."
echo ""

# Install new dependency
pip3 install lxml==4.9.3

echo ""
echo "✅ Installation complete!"
echo ""
echo "New features added:"
echo "  ✅ Batch URL processing"
echo "  ✅ Batch file uploads"
echo "  ✅ Sitemap crawling"
echo "  ✅ Image extraction from URLs"
echo ""
echo "To start the backend:"
echo "  python3 main.py"
echo ""
echo "API documentation:"
echo "  http://localhost:8000/docs"
echo ""
echo "Check CHANGES_SUMMARY.md for complete details!"
