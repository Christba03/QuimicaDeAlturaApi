# Production deploy (push images and run from registry)

## 1. Build images with fixed names

From the repo root, build so each service gets a consistent image name:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build
```

(On Windows PowerShell you can use the same command.)

This produces images:

- `quimicadealtura_api-api-gateway:prod`
- `quimicadealtura_api-auth-service:prod`
- `quimicadealtura_api-plant-service:prod`
- `quimicadealtura_api-chatbot-service:prod`
- `quimicadealtura_api-search-service:prod`
- `quimicadealtura_api-user-service:prod`
- `quimicadealtura_api-webpage:prod`
- `quimicadealtura_api-landingpage:prod`

## 2. Push images to your registry

Set your registry (Docker Hub, GitHub Container Registry, etc.) and optional tag, then run the push script.

**PowerShell (Windows):**

```powershell
$env:REGISTRY = "docker.io/yourusername"   # or ghcr.io/myorg
$env:IMAGE_TAG = "v1.0.0"                  # optional; default is "latest"
.\scripts\push-images.ps1
```

Or with parameters:

```powershell
.\scripts\push-images.ps1 -Registry "ghcr.io/myorg" -Tag "v1.0.0"
```

**Bash (Linux/macOS):**

```bash
export REGISTRY=docker.io/yourusername
export IMAGE_TAG=v1.0.0
./scripts/push-images.sh
```

- **Docker Hub:** `REGISTRY=docker.io/yourusername`
- **GitHub Container Registry:** `REGISTRY=ghcr.io/yourorg` (and log in with `docker login ghcr.io`)
- **AWS ECR:** `REGISTRY=123456789.dkr.ecr.region.amazonaws.com/myrepo`

## 3. Run production stack (pull only)

On the production host, use `docker-compose.prod.yml`. It has no `build:` steps; every app service uses `image: ${REGISTRY}/quimicadealtura_api-<service>:${IMAGE_TAG:-latest}`.

Create a production env file (e.g. `.env.production`) with at least:

```env
REGISTRY=ghcr.io/myorg
IMAGE_TAG=v1.0.0

POSTGRES_CORE_PASSWORD=...
POSTGRES_AUTH_PASSWORD=...
POSTGRES_CHATBOT_PASSWORD=...
POSTGRES_USER_PASSWORD=...
REDIS_PASSWORD=...
JWT_SECRET_KEY=...
# ... other secrets and overrides
```

Then:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

Or set variables in the environment:

```bash
export REGISTRY=ghcr.io/myorg
export IMAGE_TAG=v1.0.0
# ... other env
docker compose -f docker-compose.prod.yml up -d
```

**Note:** Schema init for Postgres still uses `./database/postgres/schemas/*`. On production you can remove those volume mounts and rely on migrations, or copy the schema files to the server.

---

## 4. Automatic build and push on push to main (GitHub Actions)

The workflow `.github/workflows/build-push.yml` builds and pushes the **in-repo** microservice images to Docker Hub on every push to `main` (or `master`). It does **not** build `webpage` or `landingpage` (their build context is outside this repo); build and push those locally or from their own repos if needed.

### One-time setup

1. **Create a Docker Hub access token**
   - Go to [Docker Hub](https://hub.docker.com) → Account Settings → Security → New Access Token.
   - Create a token with **Read, Write, Delete** (or at least Read & Write).

2. **Add repository secrets** (GitHub repo → Settings → Secrets and variables → Actions):
   - `DOCKERHUB_USERNAME`: your Docker Hub username (e.g. `christba`).
   - `DOCKERHUB_TOKEN`: the access token from step 1.

3. **Push to `main`**
   - On each push to `main` (or `master`), the workflow will:
     - Build: `api-gateway`, `auth-service`, `plant-service`, `chatbot-service`, `search-service`, `user-service`.
     - Push each image as:
       - `docker.io/<DOCKERHUB_USERNAME>/quimicadealtura_api-<service>:latest`
       - `docker.io/<DOCKERHUB_USERNAME>/quimicadealtura_api-<service>:<short-sha>` (e.g. `a1b2c3d`).

### Optional: push only when CI passes

To push only after the main CI workflow succeeds, edit `.github/workflows/build-push.yml`:

1. Change `on` to use `workflow_run` instead of `push` (see comments in the file).
2. Add the `if` condition on the job so it runs only when `workflow_run.conclusion == 'success'`.
