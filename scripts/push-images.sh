#!/usr/bin/env bash
# Tag and push all application images to a registry.
# Usage:
#   export REGISTRY=docker.io/yourusername
#   export IMAGE_TAG=v1.0.0   # optional, default latest
#   ./scripts/push-images.sh
#
# Or: REGISTRY=ghcr.io/myorg IMAGE_TAG=v1.0.0 ./scripts/push-images.sh

set -e

REGISTRY="${REGISTRY:?Set REGISTRY (e.g. docker.io/yourusername or ghcr.io/myorg)}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

IMAGES=(
  quimicadealtura_api-api-gateway:prod
  quimicadealtura_api-auth-service:prod
  quimicadealtura_api-plant-service:prod
  quimicadealtura_api-chatbot-service:prod
  quimicadealtura_api-search-service:prod
  quimicadealtura_api-user-service:prod
  quimicadealtura_api-webpage:prod
  quimicadealtura_api-landingpage:prod
)

REGISTRY="${REGISTRY%/}"
for local in "${IMAGES[@]}"; do
  name="${local%:prod}"
  remote="${REGISTRY}/${name}:${IMAGE_TAG}"
  echo "Tagging $local -> $remote"
  docker tag "$local" "$remote"
  echo "Pushing $remote"
  docker push "$remote"
done
echo "All images pushed to $REGISTRY with tag $IMAGE_TAG"
