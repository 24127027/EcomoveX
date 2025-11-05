# Test Runner Script
# This script runs all backend tests

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EcomoveX Backend Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PostgreSQL test databases exist, create if not
Write-Host "Setting up test databases..." -ForegroundColor Yellow

# Navigate to backend directory
Set-Location -Path "c:\Users\mduy\source\repos\EcomoveX\backend"

# Run tests
Write-Host "`nRunning tests..." -ForegroundColor Yellow
pytest -v --tb=short

# Check test result
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  All Tests Passed! ✓" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "  Some Tests Failed! ✗" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Write-Host "`nTest run completed." -ForegroundColor Cyan
