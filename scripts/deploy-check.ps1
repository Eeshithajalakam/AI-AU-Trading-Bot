# Post-deployment verification script
param(
    [Parameter(Mandatory=$true)]
    [string]$ApiUrl
)

$ApiUrl = $ApiUrl.TrimEnd("/")
Write-Host "Checking $ApiUrl/health ..."
try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 30
    $health | ConvertTo-Json
    Write-Host "OK: API healthy" -ForegroundColor Green
} catch {
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`nChecking /api/performance/summary ..."
try {
    $perf = Invoke-RestMethod -Uri "$ApiUrl/api/performance/summary" -TimeoutSec 30
    Write-Host "Trades: $($perf.total_trades) | Sharpe: $($perf.sharpe_ratio)" -ForegroundColor Cyan
} catch {
    Write-Host "WARN: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`nDeployment check complete."
