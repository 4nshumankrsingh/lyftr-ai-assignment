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
python -m playwright install chromium

Write-Host "Setting up frontend..." -ForegroundColor Yellow
cd frontend
npm install
cd ..

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Start the application in two separate terminals:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1 (Backend):" -ForegroundColor Yellow
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 (Frontend):" -ForegroundColor Yellow
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧪 Test URLs:" -ForegroundColor Green
Write-Host "  • Static: https://en.wikipedia.org/wiki/Artificial_intelligence" -ForegroundColor White
Write-Host "  • JS-Heavy: https://vercel.com/" -ForegroundColor White
Write-Host "  • Tabs: https://mui.com/material-ui/react-tabs/" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the servers" -ForegroundColor Yellow