#!/bin/bash

echo "=================================="
echo "Multi-Tenant RAG Chatbot Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Download NLTK data
echo ""
echo "Downloading NLTK data..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); print('NLTK data downloaded successfully')"

echo ""
echo "=================================="
echo "Setup completed successfully!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OPENAI_API_KEY"
echo "2. Activate virtual environment: source .venv/bin/activate"
echo "3. Run the application: python3 main.py"
echo ""
