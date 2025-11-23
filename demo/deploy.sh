#!/bin/bash
set -e

# E2B Hackathon Demo - Cloud Run Deployment Script
# Usage: ./deploy.sh [service-name]

SERVICE_NAME="${1:-e2b-hackathon-demo}"
PROJECT_ID="tweekitmcp-a26b6"
REGION="us-west1"
PLATFORM="managed"

echo "🚀 Deploying $SERVICE_NAME to Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

# Check if secrets are set
if [ -z "$TWEEKIT_API_KEY" ] || [ -z "$TWEEKIT_API_SECRET" ] || [ -z "$E2B_API_KEY" ] || [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  WARNING: Environment variables not fully set!"
    echo "   Make sure these are set:"
    echo "   - TWEEKIT_API_KEY"
    echo "   - TWEEKIT_API_SECRET"
    echo "   - E2B_API_KEY"
    echo "   - GROQ_API_KEY"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build environment variables string
ENV_VARS="TWEEKIT_API_KEY=$TWEEKIT_API_KEY,TWEEKIT_API_SECRET=$TWEEKIT_API_SECRET,E2B_API_KEY=$E2B_API_KEY,GROQ_API_KEY=$GROQ_API_KEY,TUNNEL_URL=https://mcp.tweekit.io/mcp"

# Add Discord webhook if configured
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    ENV_VARS="$ENV_VARS,DISCORD_WEBHOOK_URL=$DISCORD_WEBHOOK_URL,ERROR_REPORTING_ENABLED=$ERROR_REPORTING_ENABLED"
    echo "📊 Discord error reporting enabled"
fi

# Deploy to Cloud Run
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --platform "$PLATFORM" \
    --allow-unauthenticated \
    --set-env-vars "$ENV_VARS" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your demo is live at:"
gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format "value(status.url)"
echo ""
