# Auth Microservice — Endpoints & Web Usage

Use these endpoints from your **webpage** by calling the **API Gateway**. Replace `GATEWAY_URL` with your gateway base URL (e.g. `https://api.example.com` or `http://localhost:8000`).

**Base URL for auth:** `GATEWAY_URL + "/api/auth"`

All requests that need a logged-in user must send the access token in the header:
```http
Authorization: Bearer <access_token>
```

---

## 1. Authentication (no token required)

### Register
**POST** `/api/auth/api/v1/auth/register`

| Field       | Type   | Required | Constraints  |
|------------|--------|----------|--------------|
| `email`    | string | yes      | valid email  |
| `password` | string | yes      | 12–128 chars |
| `first_name` | string | yes    | 1–100 chars  |
| `last_name`  | string | yes    | 1–100 chars  |

**Success:** `201` — returns user object (id, email, first_name, last_name, is_active, roles, etc.)  
**Errors:** `400` (validation), `409` (email already registered)

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/register`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!',
    first_name: 'Jane',
    last_name: 'Doe',
  }),
});
const user = await res.json();
```

---

### Login
**POST** `/api/auth/api/v1/auth/login`

| Field     | Type   | Required | Constraints |
|----------|--------|----------|-------------|
| `email`  | string | yes      | valid email |
| `password` | string | yes    | 8–128 chars |

**Success:** `200` — either:
- **With 2FA:** `{ "challenge_token": "...", "requires_2fa": true }` → use this token in the 2FA challenge.
- **Without 2FA / trusted device:** `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 900 }`

**Errors:** `401` (invalid credentials), `429` (too many attempts)

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'MyPassword123' }),
});
const data = await res.json();
if (data.requires_2fa) {
  // Redirect to 2FA step with data.challenge_token
  window.location.href = `/verify-2fa?challenge=${encodeURIComponent(data.challenge_token)}`;
} else {
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
}
```

---

### Refresh token
**POST** `/api/auth/api/v1/auth/refresh`

| Field          | Type   | Required |
|----------------|--------|----------|
| `refresh_token` | string | yes      |

**Success:** `200` — `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 900 }`  
**Errors:** `401` (invalid or expired refresh token)

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/refresh`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token: localStorage.getItem('refresh_token') }),
});
const tokens = await res.json();
localStorage.setItem('access_token', tokens.access_token);
localStorage.setItem('refresh_token', tokens.refresh_token);
```

---

### Logout
**POST** `/api/auth/api/v1/auth/logout`

| Field           | Type   | Required |
|-----------------|--------|----------|
| `refresh_token` | string | yes      |
| `access_token`  | string | no       |

**Success:** `204` (no body)  
Sending `access_token` allows the server to blacklist it so it can’t be used again.

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/logout`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    refresh_token: localStorage.getItem('refresh_token'),
    access_token: localStorage.getItem('access_token'),
  }),
});
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

---

### JWKS (public keys)
**GET** `/api/auth/api/v1/auth/.well-known/jwks.json`

Returns the JSON Web Key Set for verifying JWT signatures. Used by backends or if you verify tokens in the frontend (usually not needed for SPA).

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/.well-known/jwks.json`);
const jwks = await res.json();
```

---

## 2. Email verification (no token required)

### Verify email
**POST** `/api/auth/api/v1/auth/verify-email`

| Field   | Type   | Required | Constraints |
|--------|--------|----------|-------------|
| `email` | string | yes      | valid email |
| `code`  | string | yes      | 6 digits    |

**Success:** `200` — `{ "message": "Email verified successfully" }`  
**Errors:** `400` (invalid/expired code), `404` (user not found)

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/verify-email`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', code: '123456' }),
});
```

---

### Resend verification code
**POST** `/api/auth/api/v1/auth/resend-verification`

| Field  | Type   | Required |
|--------|--------|----------|
| `email` | string | yes      |

**Success:** `200` — `{ "message": "If the email exists, a verification code has been sent" }`  
(Does not reveal whether the email exists.)

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/resend-verification`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' }),
});
```

---

## 3. Password reset (no token required)

### Request password reset
**POST** `/api/auth/api/v1/auth/password/reset-request`

| Field   | Type   | Required |
|--------|--------|----------|
| `email` | string | yes      |

**Success:** `200` — `{ "message": "If the email exists, a password reset code has been sent" }`

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/password/reset-request`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' }),
});
```

---

### Reset password (with code)
**POST** `/api/auth/api/v1/auth/password/reset`

| Field         | Type   | Required | Constraints  |
|--------------|--------|----------|--------------|
| `email`      | string | yes      | valid email  |
| `code`       | string | yes      | 6 digits     |
| `new_password` | string | yes    | 12–128 chars |

**Success:** `200` — `{ "message": "Password reset successfully" }`  
**Errors:** `400` (invalid code or password validation)

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/password/reset`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    code: '123456',
    new_password: 'NewSecurePass123!',
  }),
});
```

---

## 4. Two-factor authentication (2FA)

### Setup 2FA (get secret + QR)
**POST** `/api/auth/api/v1/auth/2fa/setup`  
**Auth:** Bearer token required.

| Field    | Type   | Required |
|----------|--------|----------|
| `user_id` | string (UUID) | yes |

**Success:** `200` — `{ "secret": "...", "qr_code": "<base64 image>", "uri": "otpauth://..." }`  
**Errors:** `400` (2FA already enabled), `404` (user not found)

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/2fa/setup`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  },
  body: JSON.stringify({ user_id: currentUserId }),
});
const { secret, qr_code, uri } = await res.json();
// Show QR: <img src={`data:image/png;base64,${qr_code}`} />
```

---

### Verify 2FA setup (enable 2FA)
**POST** `/api/auth/api/v1/auth/2fa/verify-setup`  
**Auth:** Bearer token required.

| Field    | Type   | Required | Constraints |
|----------|--------|----------|-------------|
| `user_id` | string (UUID) | yes | |
| `code`   | string | yes      | 6 digits (TOTP) |

**Success:** `200` — `{ "message": "...", "backup_codes": ["xxxxxxxx", ...] }` — show backup codes once.  
**Errors:** `400` (invalid code or 2FA already enabled)

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/2fa/verify-setup`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  },
  body: JSON.stringify({ user_id: currentUserId, code: '123456' }),
});
```

---

### 2FA challenge (complete login after 2FA)
**POST** `/api/auth/api/v1/auth/2fa/challenge`  
**No auth header.** Use the `challenge_token` from the login response when `requires_2fa: true`.

| Field            | Type   | Required | Constraints      |
|------------------|--------|----------|------------------|
| `challenge_token`| string | yes      | from login       |
| `code`           | string | yes      | 6 (TOTP/email) or 8 (backup) |

**Success:** `200` — `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 900 }`  
**Errors:** `400` (invalid token/code), `401` (invalid challenge)

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/2fa/challenge`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    challenge_token: urlParams.get('challenge'), // from login
    code: '123456', // from user input (TOTP or email code)
  }),
});
const tokens = await res.json();
localStorage.setItem('access_token', tokens.access_token);
localStorage.setItem('refresh_token', tokens.refresh_token);
```

---

### Request 2FA code by email
**POST** `/api/auth/api/v1/auth/2fa/request-email-code`  
**No auth header.**

| Field             | Type   | Required |
|-------------------|--------|----------|
| `challenge_token` | string | yes      |

**Success:** `200` — `{ "message": "2FA code sent to your email" }`

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/2fa/request-email-code`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ challenge_token: challengeToken }),
});
```

---

### Disable 2FA
**POST** `/api/auth/api/v1/auth/2fa/disable`  
**Auth:** Bearer token required.

| Field     | Type   | Required |
|----------|--------|----------|
| `user_id` | string (UUID) | yes |
| `password` | string | yes   |

**Success:** `200` — `{ "message": "Two-factor authentication disabled successfully" }`  
**Errors:** `400` (2FA not enabled), `401` (wrong password)

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/2fa/disable`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  },
  body: JSON.stringify({ user_id: currentUserId, password: userPassword }),
});
```

---

### Get backup codes count
**GET** `/api/auth/api/v1/auth/2fa/backup-codes?user_id=<UUID>`  
**Auth:** Bearer token required.

**Success:** `200` — `{ "remaining_backup_codes": 8 }`

```javascript
const res = await fetch(
  `${GATEWAY_URL}/api/auth/api/v1/auth/2fa/backup-codes?user_id=${currentUserId}`,
  { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` } }
);
const { remaining_backup_codes } = await res.json();
```

---

### Regenerate backup codes
**POST** `/api/auth/api/v1/auth/2fa/regenerate-backup-codes?user_id=<UUID>&password=<password>`  
**Auth:** Bearer token required.  
Send `user_id` and `password` as **query parameters**.

**Success:** `200` — `{ "message": "...", "backup_codes": ["xxxxxxxx", ...] }` — show once.

```javascript
const params = new URLSearchParams({
  user_id: currentUserId,
  password: userPassword,
});
const res = await fetch(
  `${GATEWAY_URL}/api/auth/api/v1/auth/2fa/regenerate-backup-codes?${params}`,
  {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
  }
);
const { backup_codes } = await res.json();
```

---

## 5. Sessions (auth required)

All session endpoints require: `Authorization: Bearer <access_token>`.

### List my sessions
**GET** `/api/auth/api/v1/auth/sessions/`

**Success:** `200` — array of session objects (id, ip_address, user_agent, device_info, is_trusted, created_at, etc.)

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/sessions/`, {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
});
const sessions = await res.json();
```

---

### Revoke one session
**DELETE** `/api/auth/api/v1/auth/sessions/<session_id>`

**Success:** `204` (no body)

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/sessions/${sessionId}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
});
```

---

### Revoke all sessions (except current)
**DELETE** `/api/auth/api/v1/auth/sessions/all`

**Success:** `204`

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/sessions/all`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
});
```

---

### Trust device
**POST** `/api/auth/api/v1/auth/sessions/devices/trust/<session_id>`

**Success:** `200`

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/sessions/devices/trust/${sessionId}`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
});
```

---

### Untrust device
**DELETE** `/api/auth/api/v1/auth/sessions/devices/trust/<session_id>`

**Success:** `204`

```javascript
await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/sessions/devices/trust/${sessionId}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
});
```

---

### List trusted devices
**GET** `/api/auth/api/v1/auth/sessions/devices`

**Success:** `200` — array of session objects for trusted devices.

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/sessions/devices`, {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
});
const devices = await res.json();
```

---

## 6. OAuth (Google / GitHub)

### Get authorization URL
**GET** `/api/auth/api/v1/auth/oauth/<provider>/authorize`  
`provider` = `google` or `github`.

**Success:** `200` — `{ "authorization_url": "https://...", "state": "...", "provider": "google" }`  
Store `state` (e.g. in sessionStorage) and redirect the user to `authorization_url`.

```javascript
const res = await fetch(`${GATEWAY_URL}/api/auth/api/v1/auth/oauth/google/authorize`);
const { authorization_url, state } = await res.json();
sessionStorage.setItem('oauth_state', state);
window.location.href = authorization_url;
```

---

### OAuth callback (exchange code for tokens)
**GET** `/api/auth/api/v1/auth/oauth/<provider>/callback?code=<code>&state=<state>`

Usually the user is redirected here by the provider. Your backend or a small callback page should call this URL (with the `code` and optionally `state` from the query string), then receive tokens and store them.

**Success:** `200` — `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 900 }`

```javascript
// On your OAuth callback page (e.g. /auth/callback?code=...&state=...)
const params = new URLSearchParams(window.location.search);
const code = params.get('code');
const res = await fetch(
  `${GATEWAY_URL}/api/auth/api/v1/auth/oauth/google/callback?code=${encodeURIComponent(code)}&state=${params.get('state') || ''}`
);
const tokens = await res.json();
localStorage.setItem('access_token', tokens.access_token);
localStorage.setItem('refresh_token', tokens.refresh_token);
window.location.href = '/dashboard';
```

---

## 7. Admin / internal

- **POST** `/api/auth/api/v1/auth/validate` — body `{ "token": "<access_token>" }`. Returns user_id, email, role(s). Used by the API gateway; you typically don’t call this from the webpage.
- **Users** (`/api/auth/api/v1/users/`) — list, get, create, update, delete users; unlock; force-logout; bulk actions. **Requires superuser.**
- **Roles** (`/api/auth/api/v1/roles/`) — CRUD roles. **Requires superuser.**
- **API Keys** (`/api/auth/api/v1/...`) — create/list/revoke API keys. **Requires auth.**
- **Policies** (`/api/auth/api/v1/policies/`) — create/list/delete/evaluate. **Requires auth.**
- **Audit** (`/api/auth/api/v1/audit/events`, `/api/auth/api/v1/audit/users/<user_id>/events`) — **Requires auth.**

---

## Quick reference table

| Action           | Method | Path (append to `GATEWAY_URL/api/auth`)     | Auth? |
|-----------------|--------|---------------------------------------------|-------|
| Register        | POST   | `/api/v1/auth/register`                     | No    |
| Login           | POST   | `/api/v1/auth/login`                        | No    |
| Refresh         | POST   | `/api/v1/auth/refresh`                      | No    |
| Logout          | POST   | `/api/v1/auth/logout`                       | No    |
| JWKS            | GET    | `/api/v1/auth/.well-known/jwks.json`        | No    |
| Verify email    | POST   | `/api/v1/auth/verify-email`                 | No    |
| Resend verify   | POST   | `/api/v1/auth/resend-verification`          | No    |
| Password reset request | POST | `/api/v1/auth/password/reset-request` | No    |
| Password reset  | POST   | `/api/v1/auth/password/reset`               | No    |
| 2FA setup       | POST   | `/api/v1/auth/2fa/setup`                    | Yes   |
| 2FA verify-setup| POST   | `/api/v1/auth/2fa/verify-setup`              | Yes   |
| 2FA challenge   | POST   | `/api/v1/auth/2fa/challenge`                 | No (use challenge_token) |
| 2FA email code  | POST   | `/api/v1/auth/2fa/request-email-code`        | No    |
| 2FA disable     | POST   | `/api/v1/auth/2fa/disable`                   | Yes   |
| 2FA backup count| GET    | `/api/v1/auth/2fa/backup-codes?user_id=...`  | Yes   |
| 2FA regenerate codes | POST | `/api/v1/auth/2fa/regenerate-backup-codes?user_id=...&password=...` | Yes |
| List sessions   | GET    | `/api/v1/auth/sessions/`                    | Yes   |
| Revoke session  | DELETE | `/api/v1/auth/sessions/<id>`                | Yes   |
| Revoke all      | DELETE | `/api/v1/auth/sessions/all`                 | Yes   |
| Trust device    | POST   | `/api/v1/auth/sessions/devices/trust/<id>`  | Yes   |
| Untrust device  | DELETE | `/api/v1/auth/sessions/devices/trust/<id>`  | Yes   |
| List devices    | GET    | `/api/v1/auth/sessions/devices`             | Yes   |
| OAuth authorize | GET    | `/api/v1/auth/oauth/<provider>/authorize`    | No    |
| OAuth callback  | GET    | `/api/v1/auth/oauth/<provider>/callback?code=...&state=...` | No |

---

Use `GATEWAY_URL` as your single origin (e.g. `https://api.yoursite.com`). Ensure the gateway has CORS configured for your frontend origin (e.g. `https://yoursite.com` or `http://localhost:3000`). For authenticated requests, send the header: `Authorization: Bearer <access_token>`.
