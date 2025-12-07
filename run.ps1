Write-Host "🚀 Setting up Universal Website Scraper..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\Activate.ps1
}

Write-Host "Installing Python packages..." -ForegroundColor Yellow
pip install -r backend/requirements.txt

Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
playwright install

Write-Host "Setting up frontend..." -ForegroundColor Yellow
cd frontend
npm install
npm run build
cd ..

Write-Host "✅ Setup complete! Starting server..." -ForegroundColor Green
Write-Host "🌐 Server running at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📋 Open this in your browser to use the scraper!" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

# Start the FastAPI server
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload