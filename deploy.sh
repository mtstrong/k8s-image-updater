#!/bin/bash
# Quick Deployment Script for K8s Image Updater

set -e

echo "=================================="
echo "K8s Image Updater - Quick Deploy"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN environment variable not set${NC}"
    echo "Please set it with: export GITHUB_TOKEN='your_token_here'"
    exit 1
fi

echo -e "${YELLOW}Step 1: Creating namespace...${NC}"
kubectl create namespace image-updater --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Namespace created${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating GitHub token secret...${NC}"
kubectl create secret generic github-token \
    --from-literal=token="$GITHUB_TOKEN" \
    --namespace=image-updater \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Secret created${NC}"
echo ""

echo -e "${YELLOW}Step 3: Deploying CronJob and dependencies...${NC}"
kubectl apply -f kubernetes/cronjob.yaml

echo -e "${GREEN}✓ CronJob deployed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Verifying deployment...${NC}"
kubectl get all -n image-updater

echo ""
echo -e "${GREEN}=================================="
echo "✓ Deployment Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Wait for the next scheduled run (Monday at 9 AM UTC)"
echo "2. Or trigger a manual job:"
echo "   kubectl create job --from=cronjob/k8s-image-updater manual-test -n image-updater"
echo ""
echo "3. View logs:"
echo "   kubectl logs -n image-updater job/manual-test -f"
echo ""
echo "4. Make sure the GitHub Container Registry image is public:"
echo "   https://github.com/mtstrong?tab=packages"
echo ""
