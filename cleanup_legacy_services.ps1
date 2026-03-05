# cleanup_legacy_services.ps1
# This script removes the legacy investcraft services from Google Cloud Run.

$PROJECT_ID = "market-rover"
$REGION = "us-central1"

Write-Host "⚠️  WARNING: This will delete the legacy InvestCraft services from Cloud Run." -ForegroundColor Yellow
Write-Host "Project: $PROJECT_ID ($REGION)"
Write-Host ""

# Delete Backend API
Write-Host "Deleting investcraft-api..."
gcloud run services delete investcraft-api --project $PROJECT_ID --region $REGION --quiet

# Delete Frontend UI
Write-Host "Deleting investcraft-ui..."
gcloud run services delete investcraft-ui --project $PROJECT_ID --region $REGION --quiet

Write-Host "✅ Legacy services removed." -ForegroundColor Green
