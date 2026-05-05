#!/usr/bin/env bash
# Deploy anchor-mcp to Cloud Run.
# Usage: ./deploy.sh [GCP_PROJECT_ID]   (default: anchor-electronics-mcp)
set -euo pipefail

PROJECT="${1:-anchor-electronics-mcp}"
REGION="us-west1"
SERVICE="anchor-mcp"
IMAGE="us-west1-docker.pkg.dev/${PROJECT}/anchor-mcp/server"
AR_REPO="anchor-mcp"

echo "==> Checking that project $PROJECT exists and is enabled..."
gcloud projects describe "$PROJECT" --quiet >/dev/null

echo "==> project: $PROJECT  region: $REGION"

# Create Artifact Registry repo if it doesn't exist
gcloud artifacts repositories describe "$AR_REPO" \
  --project="$PROJECT" --location="$REGION" &>/dev/null \
  || gcloud artifacts repositories create "$AR_REPO" \
       --project="$PROJECT" \
       --repository-format=docker \
       --location="$REGION" \
       --description="Anchor Electronics MCP server"

# Build and push via Cloud Build (no local Docker required)
gcloud builds submit . \
  --project="$PROJECT" \
  --tag="${IMAGE}:latest"

# Deploy to Cloud Run
gcloud run deploy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --image="${IMAGE}:latest" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=256Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \

echo
echo "==> Deployed! MCP endpoint:"
gcloud run services describe "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format="value(status.url)" \
  | sed 's|$|/mcp|'
