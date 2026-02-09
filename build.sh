#!/bin/bash
# Build and push Docker image for K8s Image Updater

set -e

# Configuration
IMAGE_NAME="k8s-image-updater"
REGISTRY="${DOCKER_REGISTRY:-docker.io}"  # Can override with environment variable
TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "Building Docker image: ${FULL_IMAGE}"
echo ""

# Build image
docker build -t "${FULL_IMAGE}" .

echo ""
echo "✓ Image built successfully"
echo ""

# Ask if user wants to push
read -p "Push image to registry? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pushing image to ${REGISTRY}..."
    docker push "${FULL_IMAGE}"
    echo ""
    echo "✓ Image pushed successfully"
    echo ""
    echo "Update your cronjob.yaml to use:"
    echo "  image: ${FULL_IMAGE}"
else
    echo "Skipping push"
    echo ""
    echo "To push later, run:"
    echo "  docker push ${FULL_IMAGE}"
fi

echo ""
echo "Done!"
