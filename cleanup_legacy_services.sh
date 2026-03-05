#!/bin/bash
# cleanup_investcraft.sh
# This script removes the legacy investcraft services from Google Cloud Run.

PROJECT_ID="market-rover"
REGION="us-central1"

echo "⚠️  WARNING: This will delete the legacy InvestCraft services from Cloud Run."
echo "Project: $PROJECT_ID ($REGION)"
echo ""

# Delete Backend API
echo "Deleting investcraft-api..."
gcloud run services delete investcraft-api --project $PROJECT_ID --region $REGION --quiet

# Delete Frontend UI
echo "Deleting investcraft-ui..."
gcloud run services delete investcraft-ui --project $PROJECT_ID --region $REGION --quiet

echo "✅ Legacy services removed."
