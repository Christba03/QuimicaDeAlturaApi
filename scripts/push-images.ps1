# Tag and push all application images to a registry.
# Usage:
#   $env:REGISTRY = "docker.io/yourusername"
#   $env:IMAGE_TAG = "v1.0.0"   # optional, default "latest"
#   .\scripts\push-images.ps1
#
# Or: .\scripts\push-images.ps1 -Registry "ghcr.io/myorg" -Tag "v1.0.0"

param(
    [Parameter(Mandatory = $true)]
    [string]$Registry,
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

$images = @(
    "quimicadealtura_api-api-gateway:prod",
    "quimicadealtura_api-auth-service:prod",
    "quimicadealtura_api-plant-service:prod",
    "quimicadealtura_api-chatbot-service:prod",
    "quimicadealtura_api-search-service:prod",
    "quimicadealtura_api-user-service:prod",
    "quimicadealtura_api-webpage:prod",
    "quimicadealtura_api-landingpage:prod"
)

$registryTrim = $Registry.TrimEnd('/')
foreach ($local in $images) {
    $name = $local -replace ':prod$', ''
    $remote = "${registryTrim}/${name}:${Tag}"
    Write-Host "Tagging $local -> $remote"
    docker tag $local $remote
    if (-not $?) { throw "docker tag failed" }
    Write-Host "Pushing $remote"
    docker push $remote
    if (-not $?) { throw "docker push failed" }
}
Write-Host "All images pushed to $registryTrim with tag $Tag"
