# Reset Core DB (fix "database: disconnected")

If plant-service health shows `database: disconnected`, the core PostgreSQL volume was likely created with a different password than in your current `.env`.

**Option A – Reset core DB volume (recommended for dev)**

From the project root:

```powershell
# Stop and remove only the core DB container and its volume
docker compose stop plant-service postgres-core
docker compose rm -f postgres-core
docker volume rm quimicadealturaapi_postgres_core_data

# Start postgres-core again (creates a new volume with current .env password)
docker compose up -d postgres-core

# Wait for healthy (e.g. 10–15 seconds), then start plant-service
docker compose up -d plant-service
```

Then check:

```powershell
Invoke-RestMethod -Uri http://localhost:8002/health
```

**Option B – Use the password the volume was created with**

If you know the password that was used when the volume was first created (e.g. `dev_core_password`), set that in `.env`:

```env
POSTGRES_CORE_PASSWORD=dev_core_password
```

Restart plant-service:

```powershell
docker compose up -d plant-service
```
