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

# Auto-load environment variables from .envrc if it exists
# This prevents the recurring issue of missing API keys
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVRC_PATH="$PROJECT_ROOT/.envrc"

if [ -f "$ENVRC_PATH" ]; then
    echo "📋 Loading environment variables from .envrc..."
    # Source the .envrc file, but filter out non-export lines and echo statements
    set -a  # Automatically export all variables
    source "$ENVRC_PATH" 2>/dev/null || true
    set +a
    echo "✅ Environment variables loaded"
    echo ""
else
    echo "⚠️  No .envrc file found at $ENVRC_PATH"
    echo ""
fi

# Check if secrets are set
if [ -z "$TWEEKIT_API_KEY" ] || [ -z "$TWEEKIT_API_SECRET" ] || [ -z "$E2B_API_KEY" ] || [ -z "$GROQ_API_KEY" ]; then
    echo "❌ ERROR: Required environment variables are missing!"
    echo "   Make sure these are set in .envrc:"
    echo "   - TWEEKIT_API_KEY"
    echo "   - TWEEKIT_API_SECRET"
    echo "   - E2B_API_KEY"
    echo "   - GROQ_API_KEY"
    echo ""
    echo "   Create a .envrc file in the project root with these variables."
    exit 1
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
    --source demo \
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
