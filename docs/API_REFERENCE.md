# Química de Altura API — Frontend Integration Reference

This document lists **all API Gateway endpoints**, required **headers**, and example **JSON request/response bodies** for frontend integration.

> **Source of truth:** the live OpenAPI is served by the gateway at `GET /docs` (Swagger UI) and `GET /openapi.json` (FastAPI default).

---

## Base URL (API Gateway)

- **Gateway base:** `GATEWAY_URL` (default local dev: `http://localhost:8000`)
- **All endpoints below are called on the gateway** and start with `/api/...` (except gateway health/docs).

---

## Common headers

- **JSON requests**
  - `Content-Type: application/json`
  - `Accept: application/json` (optional)
- **Authenticated endpoints**
  - `Authorization: Bearer <access_token>`

> The gateway forwards some headers downstream and injects internal `X-User-*` headers to services. The frontend **does not need** to set `X-User-*`.

---

## Common error responses (convention)

Most endpoints return FastAPI-style errors:

```json
{ "detail": "Some error message" }
```

Auth login can return a structured detail for “email not verified”:

```json
{
  "detail": {
    "code": "email_not_verified",
    "message": "Verify your email to sign in. Check your inbox or request a new code."
  }
}
```

---

## API Gateway (direct on gateway)

### Health
- **GET** `/health`
- **Response 200**

```json
{ "status": "healthy", "service": "mp-api-gateway" }
```

### Health (downstream probe)
- **GET** `/health/details`
- **Response 200**

```json
{
  "status": "healthy",
  "service": "mp-api-gateway",
  "dependencies": [
    { "name": "auth", "status": "healthy", "status_code": 200 }
  ]
}
```

### API docs
- **GET** `/docs` (Swagger UI)
- **GET** `/openapi.json` (OpenAPI JSON)

---

## Auth Service (gateway prefix: `/api/auth`)

**Base:** `GATEWAY_URL + "/api/auth"`

### 1) Register
- **POST** `/api/auth/api/v1/auth/register`
- **Auth:** No
- **Request**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Doe"
}
```

- **Response 201** (`UserResponse`)

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "roles": [
    { "id": "00000000-0000-0000-0000-000000000000", "name": "user", "description": null }
  ]
}
```

### 2) Login
- **POST** `/api/auth/api/v1/auth/login`
- **Auth:** No
- **Request**

```json
{ "email": "user@example.com", "password": "MyPassword123" }
```

- **Response 200 (no 2FA / trusted device)** (`TokenResponse`)

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

- **Response 200 (2FA required)**

```json
{ "challenge_token": "jwt-access-token", "requires_2fa": true }
```

### 3) Refresh token
- **POST** `/api/auth/api/v1/auth/refresh`
- **Auth:** No
- **Request**

```json
{ "refresh_token": "jwt-refresh-token" }
```

- **Response 200** (`TokenResponse`)

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token-rotated",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4) Logout
- **POST** `/api/auth/api/v1/auth/logout`
- **Auth:** No
- **Request**

```json
{
  "refresh_token": "jwt-refresh-token",
  "access_token": "jwt-access-token"
}
```

- **Response 204:** no body

### 5) Validate access token (get user_id + roles)
- **POST** `/api/auth/api/v1/auth/validate`
- **Auth:** No (used by gateway/services; frontend may call it)
- **Request**

```json
{ "token": "jwt-access-token" }
```

- **Response 200**

```json
{
  "user_id": "00000000-0000-0000-0000-000000000000",
  "email": "user@example.com",
  "role": "user",
  "roles": ["user"]
}
```

### 6) JWKS (public keys)
- **GET** `/api/auth/api/v1/auth/.well-known/jwks.json`
- **Auth:** No
- **Response 200:** JSON Web Key Set

---

## Email verification (Auth service)

### Verify email
- **POST** `/api/auth/api/v1/auth/verify-email`
- **Auth:** No
- **Request**

```json
{ "email": "user@example.com", "code": "123456" }
```

- **Response 200**

```json
{ "message": "Email verified successfully" }
```

### Resend verification code
- **POST** `/api/auth/api/v1/auth/resend-verification`
- **Auth:** No
- **Request**

```json
{ "email": "user@example.com" }
```

- **Response 200**

```json
{ "message": "If the email exists, a verification code has been sent" }
```

---

## Password reset (Auth service)

### Request reset
- **POST** `/api/auth/api/v1/auth/password/reset-request`
- **Auth:** No
- **Request**

```json
{ "email": "user@example.com" }
```

- **Response 200**

```json
{ "message": "If the email exists, a password reset code has been sent" }
```

### Reset password
- **POST** `/api/auth/api/v1/auth/password/reset`
- **Auth:** No
- **Request**

```json
{ "email": "user@example.com", "code": "123456", "new_password": "NewSecurePass123!" }
```

- **Response 200**

```json
{ "message": "Password reset successfully" }
```

---

## Two-factor authentication (Auth service)

### Setup 2FA (get secret + QR)
- **POST** `/api/auth/api/v1/auth/2fa/setup`
- **Auth:** Yes (Bearer)
- **Request**

```json
{ "user_id": "00000000-0000-0000-0000-000000000000" }
```

- **Response 200**

```json
{
  "secret": "BASE32SECRET",
  "qr_code": "<base64_png>",
  "uri": "otpauth://totp/..."
}
```

### Verify 2FA setup (enable)
- **POST** `/api/auth/api/v1/auth/2fa/verify-setup`
- **Auth:** Yes (Bearer)
- **Request**

```json
{ "user_id": "00000000-0000-0000-0000-000000000000", "code": "123456" }
```

- **Response 200**

```json
{ "message": "2FA enabled", "backup_codes": ["XXXXXXXX", "YYYYYYYY"] }
```

### 2FA challenge (complete login)
- **POST** `/api/auth/api/v1/auth/2fa/challenge`
- **Auth:** No
- **Request**

```json
{ "challenge_token": "jwt-challenge-token", "code": "123456" }
```

- **Response 200** (`TokenResponse`)

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Request 2FA code by email
- **POST** `/api/auth/api/v1/auth/2fa/request-email-code`
- **Auth:** No
- **Request**

```json
{ "challenge_token": "jwt-challenge-token" }
```

- **Response 200**

```json
{ "message": "2FA code sent to your email" }
```

### Disable 2FA
- **POST** `/api/auth/api/v1/auth/2fa/disable`
- **Auth:** Yes (Bearer)
- **Request**

```json
{ "user_id": "00000000-0000-0000-0000-000000000000", "password": "MyPassword123" }
```

- **Response 200**

```json
{ "message": "2FA disabled" }
```

### Get backup codes
- **GET** `/api/auth/api/v1/auth/2fa/backup-codes?user_id=<UUID>`
- **Auth:** Yes (Bearer)
- **Response 200**

```json
{ "backup_codes": ["XXXXXXXX", "YYYYYYYY"], "count": 2 }
```

### Regenerate backup codes
- **POST** `/api/auth/api/v1/auth/2fa/regenerate-backup-codes?user_id=<UUID>&password=<password>`
- **Auth:** Yes (Bearer)
- **Response 200**

```json
{ "backup_codes": ["XXXXXXXX", "YYYYYYYY"], "count": 2 }
```

---

## Sessions (Auth service)

> These endpoints require `Authorization: Bearer <access_token>`.

- **GET** `/api/auth/api/v1/auth/sessions/`
- **DELETE** `/api/auth/api/v1/auth/sessions/{session_id}`
- **DELETE** `/api/auth/api/v1/auth/sessions/all`
- **POST** `/api/auth/api/v1/auth/sessions/devices/trust/{session_id}`
- **DELETE** `/api/auth/api/v1/auth/sessions/devices/trust/{session_id}`
- **GET** `/api/auth/api/v1/auth/sessions/devices`

Response objects are “session” records (device/ip/expiry). Exact fields are in the service OpenAPI (`/docs`).

---

## OAuth (Auth service)

- **GET** `/api/auth/api/v1/auth/oauth/{provider}/authorize`
- **GET** `/api/auth/api/v1/auth/oauth/{provider}/callback`

These endpoints support social login flows. Use the gateway OpenAPI for exact query params per provider.

---

## User + Role management (Auth service)

> Admin-oriented endpoints. Auth required. Exact request bodies are in OpenAPI.

### Users
- **GET** `/api/auth/api/v1/users/`
- **GET** `/api/auth/api/v1/users/{user_id}`
- **POST** `/api/auth/api/v1/users/` (body: `UserCreate`)
- **PUT** `/api/auth/api/v1/users/{user_id}` (body: `UserUpdate`)
- **DELETE** `/api/auth/api/v1/users/{user_id}`
- **POST** `/api/auth/api/v1/users/{user_id}/unlock`
- **POST** `/api/auth/api/v1/users/{user_id}/force-logout`
- **POST** `/api/auth/api/v1/users/bulk-action`

### Roles
- **GET** `/api/auth/api/v1/roles/`
- **GET** `/api/auth/api/v1/roles/{role_id}`
- **POST** `/api/auth/api/v1/roles/`
- **PUT** `/api/auth/api/v1/roles/{role_id}`
- **DELETE** `/api/auth/api/v1/roles/{role_id}`

---

## API Keys (Auth service)

> Auth required for “my keys” endpoints.

### Create API key (returns plaintext key once)
- **POST** `/api/auth/api/v1/users/{user_id}/api-keys`
- **Auth:** Yes (Bearer)
- **Request**

```json
{ "name": "My Key", "scopes": ["read"], "expires_at": "2026-12-31T00:00:00Z" }
```

- **Response 201**

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "name": "My Key",
  "key": "raw_api_key_returned_once",
  "key_prefix": "mpk_...",
  "scopes": ["read"],
  "expires_at": "2026-12-31T00:00:00Z",
  "created_at": "2026-01-01T00:00:00Z"
}
```

### List API keys
- **GET** `/api/auth/api/v1/users/{user_id}/api-keys`
- **Auth:** Yes (Bearer)
- **Response 200** (no plaintext key)

### Revoke API key
- **DELETE** `/api/auth/api/v1/users/{user_id}/api-keys/{key_id}`
- **Auth:** Yes (Bearer)
- **Response 204**

### Validate API key (gateway/services use)
- **POST** `/api/auth/api/v1/api-keys/validate`
- **Auth:** No
- **Request**

```json
{ "key": "raw_api_key" }
```

- **Response 200**

```json
{ "valid": true, "user_id": "00000000-0000-0000-0000-000000000000", "scopes": ["read"] }
```

---

## Policies + Audit + Settings (Auth service)

### ABAC Policies
- **POST** `/api/auth/api/v1/policies/`
- **GET** `/api/auth/api/v1/policies/`
- **DELETE** `/api/auth/api/v1/policies/{policy_id}`
- **POST** `/api/auth/api/v1/policies/evaluate`

### Security Audit (events)
- **GET** `/api/auth/api/v1/audit/events`
- **GET** `/api/auth/api/v1/audit/users/{user_id}/events`

### Dashboard Settings
- **GET** `/api/settings/api/v1/settings/`
- **PUT** `/api/settings/api/v1/settings/`

### Audit-log (dashboard feed)
- **GET** `/api/audit-log/api/v1/audit-log/`
- **GET** `/api/audit-log/api/v1/audit-log/{event_id}`

---

## Plant Service (gateway prefixes: `/api/plants`, `/api/compounds`, ...)

The gateway routes many prefixes to the same Plant service. For consistency, the examples below use the **canonical** gateway base:

- **Base:** `GATEWAY_URL + "/api/plants"`

### Pagination convention (many list endpoints)

- `page`: integer (default 1)
- `size` or `page_size`: integer (default 20)

Responses typically include:

```json
{ "items": [], "total": 0, "page": 1, "size": 20, "pages": 0 }
```

---

## Plants

### List plants
- **GET** `/api/plants/plants/?page=1&size=20`
- **Response 200** (`PlantListResponse`)

```json
{
  "items": [
    {
      "id": "00000000-0000-0000-0000-000000000000",
      "scientific_name": "Plantus example",
      "common_name": "Example plant",
      "family": "Asteraceae",
      "genus": "Plantus",
      "status": "draft",
      "properties": null,
      "image_url": null,
      "region": null,
      "category": null,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### Get plant detail
- **GET** `/api/plants/plants/{plant_id}`
- **Response 200** (`PlantDetail`) includes `compounds`, `activities`, `versions`.

### Create plant
- **POST** `/api/plants/plants/`
- **Request** (`PlantCreate`) — see fields in `PlantBase` (scientific_name, common_name, family, …)
- **Response 201** (`PlantResponse`)

### Update plant
- **PUT** `/api/plants/plants/{plant_id}`
- **Request** (`PlantUpdate`) — partial update fields
- **Response 200** (`PlantResponse`)

### Delete plant
- **DELETE** `/api/plants/plants/{plant_id}`
- **Response 204**

---

## Compounds

- **GET** `/api/plants/compounds/`
- **GET** `/api/plants/compounds/{compound_id}`
- **POST** `/api/plants/compounds/` (body: `CompoundCreate`)
- **PUT** `/api/plants/compounds/{compound_id}` (body: `CompoundUpdate`)
- **DELETE** `/api/plants/compounds/{compound_id}`

### Link a compound to a plant
- **POST** `/api/plants/compounds/link`
- **Request** (`PlantCompoundCreate`)

```json
{
  "plant_id": "00000000-0000-0000-0000-000000000000",
  "compound_id": "00000000-0000-0000-0000-000000000000",
  "plant_part": "leaf",
  "concentration": "1.2 mg/g",
  "extraction_method": "infusion",
  "reference": "Some paper"
}
```

- **Response 201** (`PlantCompoundResponse`)

### Unlink a compound from a plant
- **DELETE** `/api/plants/compounds/link/{plant_id}/{compound_id}`
- **Response 204**

### List compounds for a plant
- **GET** `/api/plants/compounds/plant/{plant_id}`
- **Response 200** `list[PlantCompoundResponse]`

---

## Activities

Activities schemas are defined inline in the endpoint module.

- **GET** `/api/plants/activities/`
- **GET** `/api/plants/activities/{activity_id}`
- **POST** `/api/plants/activities/` (body: `ActivityCreate`)
- **PUT** `/api/plants/activities/{activity_id}` (body: `ActivityUpdate`)
- **DELETE** `/api/plants/activities/{activity_id}`

Example create request:

```json
{
  "plant_id": "00000000-0000-0000-0000-000000000000",
  "activity_type": "anti-inflammatory",
  "description": "Observed in vitro",
  "evidence_level": "TRADITIONAL",
  "target_condition": "inflammation",
  "reference_doi": "10.1234/example"
}
```

---

## Articles

- **GET** `/api/plants/articles/`
- **GET** `/api/plants/articles/{article_id}`
- **POST** `/api/plants/articles/` (body: `ArticleCreate`)
- **PUT** `/api/plants/articles/{article_id}` (body: `ArticleUpdate`)
- **DELETE** `/api/plants/articles/{article_id}`

### Enrich article (IDs, OA info)
- **POST** `/api/plants/articles/{article_id}/enrich`
- **Response 200** (`EnrichmentResponse`)

### Citation
- **GET** `/api/plants/articles/{article_id}/citation`
- **Response 200** (`CitationResponse`)

### Full text ingest
- **POST** `/api/plants/articles/{article_id}/full-text`
- **Response 200** (`FullTextResponse`)

### Import from PubMed
- **POST** `/api/plants/articles/import`
- **Request** (`PubMedImportRequest`)

```json
{ "query": "mexican medicinal plants", "max_results": 10 }
```

- **Response 200** (`PubMedImportResponse`)

---

## Verification workflow (plants)

- **POST** `/api/plants/verification/{plant_id}/submit`
- **POST** `/api/plants/verification/{plant_id}/approve` (body: `{ "reviewer_id": "<UUID>" }`)
- **POST** `/api/plants/verification/{plant_id}/reject` (body: `{ "reviewer_id": "<UUID>", "reason": "..." }`)
- **POST** `/api/plants/verification/{plant_id}/revert`

All return:

```json
{ "plant_id": "<UUID>", "status": "verified", "message": "..." }
```

---

## Ethnobotanical / Genomic data / Ontology terms / Regional availability / Drug references

Each resource follows CRUD:

- **GET** `/{resource}/`
- **GET** `/{resource}/{item_id}`
- **POST** `/{resource}/` (body: `{Resource}Create`)
- **PUT** `/{resource}/{item_id}` (body: `{Resource}Update`)
- **DELETE** `/{resource}/{item_id}`

Resources (full gateway paths when using base `GATEWAY_URL + "/api/plants"`):

- `/ethnobotanical`
- `/genomic-data`
- `/ontology-terms`
- `/regional-availability`
- `/drug-references`

The exact JSON fields are defined in these schema modules:

- `services/plant-service/src/schemas/ethnobotanical.py`
- `services/plant-service/src/schemas/genomic_data.py`
- `services/plant-service/src/schemas/ontology_term.py`
- `services/plant-service/src/schemas/regional_availability.py`
- `services/plant-service/src/schemas/drug_reference.py`

---

## Inference jobs

- **GET** `/api/plants/inference-jobs/`
- **GET** `/api/plants/inference-jobs/{item_id}`
- **POST** `/api/plants/inference-jobs/` (body: `InferenceJobCreate`)
- **PUT** `/api/plants/inference-jobs/{item_id}` (body: `InferenceJobUpdate`)
- **DELETE** `/api/plants/inference-jobs/{item_id}`

---

## Data pipelines

- **GET** `/api/plants/data-pipelines/`
- **GET** `/api/plants/data-pipelines/{item_id}`
- **POST** `/api/plants/data-pipelines/` (body: `DataPipelineCreate`)
- **PUT** `/api/plants/data-pipelines/{item_id}` (body: `DataPipelineUpdate`)
- **DELETE** `/api/plants/data-pipelines/{item_id}`
- **POST** `/api/plants/data-pipelines/{item_id}/trigger`

---

## Image logs

- **GET** `/api/plants/image-logs/`
- **GET** `/api/plants/image-logs/{item_id}`
- **PUT** `/api/plants/image-logs/{item_id}` (body: `ImageLogUpdate`)
- **DELETE** `/api/plants/image-logs/{item_id}`

---

## Moderation

- **GET** `/api/plants/moderation/`
- **GET** `/api/plants/moderation/{item_id}`
- **POST** `/api/plants/moderation/` (body: `ModerationCreate`)
- **PUT** `/api/plants/moderation/{item_id}` (body: `ModerationUpdate`)
- **DELETE** `/api/plants/moderation/{item_id}`
- **PUT** `/api/plants/moderation/{item_id}/approve` (body: `ModerationApproveRequest`)
- **PUT** `/api/plants/moderation/{item_id}/reject` (body: `ModerationRejectRequest`)

---

## Query logs

- **GET** `/api/plants/query-logs/`
- **GET** `/api/plants/query-logs/{item_id}`
- **PUT** `/api/plants/query-logs/{item_id}` (body: `QueryLogFlagUpdate`)
- **DELETE** `/api/plants/query-logs/{item_id}`

---

## Analytics (read-only)

- **GET** `/api/plants/analytics/biodiversity`
- **GET** `/api/plants/analytics/phytochemical`
- **GET** `/api/plants/analytics/evidence-quality`
- **GET** `/api/plants/analytics/genomic-tracker`
- **GET** `/api/plants/analytics/epidemiology`
- **GET** `/api/plants/analytics/drug-analogs`
- **GET** `/api/plants/analytics/research-gaps`

---

## External APIs registry

- **GET** `/api/plants/external-apis/`
- **GET** `/api/plants/external-apis/{item_id}`
- **POST** `/api/plants/external-apis/` (body: `ExternalApiCreate`)
- **PUT** `/api/plants/external-apis/{item_id}` (body: `ExternalApiUpdate`)
- **DELETE** `/api/plants/external-apis/{item_id}`

---

## Model versions

- **GET** `/api/plants/model-versions/`
- **GET** `/api/plants/model-versions/{item_id}`
- **POST** `/api/plants/model-versions/` (body: `ModelVersionCreate`)
- **PUT** `/api/plants/model-versions/{item_id}` (body: `ModelVersionUpdate`)
- **DELETE** `/api/plants/model-versions/{item_id}`
- **PUT** `/api/plants/model-versions/{item_id}/activate`
- **PUT** `/api/plants/model-versions/{item_id}/rollback`

---

## User Service (gateway prefix: `/api/users`)

**Base:** `GATEWAY_URL + "/api/users"`

> These endpoints are user-scoped (“me”) and generally should be called with `Authorization: Bearer <access_token>`.

### Profile
- **GET** `/api/users/profile/me` → `UserProfileResponse`
- **PUT** `/api/users/profile/me` (body: `UserProfileUpdate`) → `UserProfileResponse`
- **GET** `/api/users/profile/me/preferences` → `UserPreferences`
- **PUT** `/api/users/profile/me/preferences` (body: `UserPreferences`) → `UserPreferences`

Example preferences body:

```json
{
  "language": "es",
  "measurement_unit": "metric",
  "altitude_unit": "meters",
  "notifications_enabled": true,
  "newsletter_subscribed": false,
  "default_region": null,
  "theme": "light"
}
```

### Favorites
- **GET** `/api/users/favorites`
- **POST** `/api/users/favorites`
- **DELETE** `/api/users/favorites/{plant_id}`
- **GET** `/api/users/favorites/{plant_id}/check`

### Usage reports
- **POST** `/api/users/usage-reports` (body: `UsageReportCreate`) → `UsageReportResponse`
- **GET** `/api/users/usage-reports` → `UsageReportListResponse`
- **GET** `/api/users/usage-reports/{report_id}` → `UsageReportResponse`
- **DELETE** `/api/users/usage-reports/{report_id}` → 204

### History
- **GET** `/api/users/history/searches`
- **POST** `/api/users/history/searches`
- **DELETE** `/api/users/history/searches`
- **GET** `/api/users/history/views`
- **POST** `/api/users/history/views`
- **DELETE** `/api/users/history/views`

---

## Search Service (gateway prefix: `/api/search`)

**Base:** `GATEWAY_URL + "/api/search"`

### Search
- **GET** `/api/search/api/v1/search/?q=<query>&page=1&page_size=20`
- **Response 200:** returns a search results object (see OpenAPI for exact shape).

### Facets
- **GET** `/api/search/api/v1/search/facets?q=<optional>`

### Autocomplete
- **GET** `/api/search/api/v1/autocomplete/?q=<query>`
- **GET** `/api/search/api/v1/autocomplete/popular`

### Recommendations
- **GET** `/api/search/api/v1/recommendations/plants/{plant_id}/related`
- **GET** `/api/search/api/v1/recommendations/compounds/{compound_id}/similar`
- **GET** `/api/search/api/v1/recommendations/user/{user_id}`

---

## Chatbot Service (gateway prefix: `/api/chatbot`)

**Base:** `GATEWAY_URL + "/api/chatbot"`

### Send chat message
- **POST** `/api/chatbot/api/v1/chat/send`
- **Request** (`ChatRequest`)

```json
{
  "user_id": "00000000-0000-0000-0000-000000000000",
  "conversation_id": null,
  "message": "¿Qué plantas ayudan para el resfriado?",
  "language": "es"
}
```

- **Response 200** (`ChatResponse`)

```json
{
  "conversation_id": "00000000-0000-0000-0000-000000000000",
  "message_id": "00000000-0000-0000-0000-000000000000",
  "response": "…",
  "intent": null,
  "entities": null,
  "sources": null,
  "suggested_replies": null,
  "created_at": "2026-01-01T00:00:00Z"
}
```

### Quick replies
- **GET** `/api/chatbot/api/v1/chat/quick-replies`
- **Response 200** (`QuickReplyResponse`)

### Conversations
- **GET** `/api/chatbot/api/v1/conversations/`
- **GET** `/api/chatbot/api/v1/conversations/{conversation_id}`
- **GET** `/api/chatbot/api/v1/conversations/{conversation_id}/messages`
- **DELETE** `/api/chatbot/api/v1/conversations/{conversation_id}`

### Feedback
- **POST** `/api/chatbot/api/v1/feedback/` (body: `FeedbackRequest`) → `FeedbackResponse`
- **GET** `/api/chatbot/api/v1/feedback/stats` → `FeedbackStatsResponse`

### WebSocket (streaming chat)
- **WS** `ws://<gateway-host>/api/chatbot/ws/chat/{client_id}`

Payload sent over the socket:

```json
{
  "user_id": "00000000-0000-0000-0000-000000000000",
  "conversation_id": null,
  "message": "Hola",
  "language": "es"
}
```

Server messages:
- `{ "type": "stream_start", "message_id": "..." }`
- `{ "type": "stream_chunk", "message_id": "...", "content": "..." }`
- `{ "type": "stream_end", "message_id": "...", "content": "full response" }`
- `{ "type": "error", "detail": "..." }`

