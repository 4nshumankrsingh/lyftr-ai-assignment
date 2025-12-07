#!/bin/bash

echo "========================================="
echo "Lyftr AI Universal Website Scraper"
echo "========================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>/dev/null || python --version)
if ! [[ $python_version =~ Python\ 3\.(1[0-9]|[2-9][0-9]) ]]; then
    echo "ERROR: Python 3.10+ required. Found: $python_version"
    echo "Please install Python 3.10 or higher from https://www.python.org/"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install chromium

# Install frontend dependencies if package.json exists
if [ -f "frontend/package.json" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo "========================================="
echo "Setup complete!"
echo ""
echo "To start the application:"
echo "1. Start backend: cd backend && uvicorn app.main:app --reload --port 8000"
echo "2. Start frontend: cd frontend && npm run dev"
echo ""
echo "Access points:"
echo "- Frontend UI: http://localhost:5173"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "========================================="