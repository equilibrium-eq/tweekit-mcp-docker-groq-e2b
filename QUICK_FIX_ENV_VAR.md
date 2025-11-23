# Quick Fix: Set Environment Variable in Cloud Run

## The Problem

The `FORWARDED_ALLOW_IPS` environment variable from the Dockerfile is not being applied to the Cloud Run service. Cloud Run ignores Dockerfile ENV declarations and requires explicit configuration.

## The Solution

Set the environment variable explicitly during Cloud Run deployment.

## Quick Fix Command

```bash
# Set the environment variable on the existing service
gcloud run services update tweekit-mcp \
  --update-env-vars FORWARDED_ALLOW_IPS=* \
  --region=us-west1 \
  --project=tweekitmcp-a26b6
```

**Time**: ~2-3 minutes

## Then Test

```bash
# Verify it's set
gcloud run services describe tweekit-mcp \
  --region=us-west1 \
  --project=tweekitmcp-a26b6 \
  --format="yaml(spec.template.spec.containers[0].env)"

# Should show:
# - name: FORWARDED_ALLOW_IPS
#   value: '*'

# Test the endpoint
curl -L -v https://mcp.tweekit.io/mcp/ 2>&1 | grep HTTP | head -5

# Test FastMCP Client
python3 -c "
import asyncio
from fastmcp import Client

async def test():
    async with Client('https://mcp.tweekit.io/mcp/') as c:
        tools = await c.list_tools()
        print(f'✓ {len(tools)} tools')

asyncio.run(test())
"
```

## Alternative: Update Deployment Script

For future deployments, modify `scripts/deploy_cloud_run.sh` to include environment variables.

Or create an env file and use `--env-vars-file` flag:

```bash
# Create env.yaml
cat > env.yaml <<EOF
FORWARDED_ALLOW_IPS: "*"
EOF

# Deploy with env file
bash scripts/deploy_cloud_run.sh prod --version 1.6.02 --env-file env.yaml
```

## Why This is Needed

Cloud Run doesn't automatically use Dockerfile ENV declarations. You must explicitly set environment variables either:
1. Via `--update-env-vars` flag
2. Via `--env-vars-file` during deployment
3. Via the Cloud Run Console UI

The Dockerfile ENV only affects the container image itself, not the Cloud Run service configuration.
