# Auth — Frontend guide (no cookies)

Use the **API Gateway** for all requests. Store tokens in **localStorage** and send the access token in the **Authorization** header.

---

## Base URL and header

- **Auth base:** `GATEWAY_URL + "/api/auth"`
- **Authenticated requests:** send the access token in the header:
  ```http
  Authorization: Bearer <access_token>
  ```

Replace `GATEWAY_URL` with your gateway (e.g. `https://api.example.com` or `http://localhost:8000`).

---

## Endpoints summary

| Step | Method | Path | Auth | Body (JSON) | Success |
|------|--------|------|------|-------------|---------|
| Register | POST | `/api/auth/api/v1/auth/register` | No | `email`, `password`, `first_name`, `last_name` | 201 user |
| Verify email | POST | `/api/auth/api/v1/auth/verify-email` | No | `email`, `code` | 200 |
| Resend verification | POST | `/api/auth/api/v1/auth/resend-verification` | No | `email` | 200 |
| Login | POST | `/api/auth/api/v1/auth/login` | No | `email`, `password` | 200 tokens or 2FA challenge |
| 2FA challenge | POST | `/api/auth/api/v1/auth/2fa/challenge` | No | `challenge_token`, `code` | 200 tokens |
| Refresh | POST | `/api/auth/api/v1/auth/refresh` | No | `refresh_token` | 200 tokens |
| Logout | POST | `/api/auth/api/v1/auth/logout` | No | `refresh_token`, optional `access_token` | 204 |
| Validate token | POST | `/api/auth/api/v1/auth/validate` | No | `token` (access_token) | 200 user_id, email, role, roles |

---

## Steps to use on the frontend

### 1. App init (after load)

- Read `access_token` and `refresh_token` from `localStorage`.
- If you have a refresh token, you can call **Refresh** to get a new access token (e.g. after a reload).
- Optional: call **Validate** with the access token to get `user_id`, `email`, `role`, `roles` for guards and UI.

### 2. Register

```http
POST {GATEWAY_URL}/api/auth/api/v1/auth/register
Content-Type: application/json

{ "email": "...", "password": "...", "first_name": "...", "last_name": "..." }
```

- **201:** User created. Redirect to “verify email” page and ask user to enter the code from email.
- **400:** Validation error. **409:** Email already registered.

### 3. Verify email (and resend)

- **Submit code:**  
  `POST {GATEWAY_URL}/api/auth/api/v1/auth/verify-email`  
  Body: `{ "email": "...", "code": "123456" }`  
  **200:** Verified → redirect to login.

- **Resend code:**  
  `POST {GATEWAY_URL}/api/auth/api/v1/auth/resend-verification`  
  Body: `{ "email": "..." }`  
  **200:** “If the email exists, a code has been sent.”

### 4. Login

```http
POST {GATEWAY_URL}/api/auth/api/v1/auth/login
Content-Type: application/json

{ "email": "...", "password": "..." }
```

- **200** and **no** `requires_2fa`: response has `access_token`, `refresh_token`, `token_type`, `expires_in`.  
  → Save to localStorage and redirect to app:
  ```javascript
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  // optional: localStorage.setItem('expires_in', String(data.expires_in));
  ```
- **200** and `requires_2fa: true`: response has `challenge_token`.  
  → Redirect to 2FA page and use that token in the **2FA challenge** (step 5).
- **403** and `detail.code === "email_not_verified"`: redirect to verify-email page.
- **401:** Invalid credentials. **429:** Too many attempts.

### 5. 2FA challenge (only when login returned requires_2fa)

```http
POST {GATEWAY_URL}/api/auth/api/v1/auth/2fa/challenge
Content-Type: application/json

{ "challenge_token": "<from login>", "code": "123456" }
```

- **200:** Same token shape as login → store `access_token` and `refresh_token` in localStorage.

### 6. Refresh token (before access token expires or on 401)

- Use when the access token is about to expire (e.g. refresh ~5 min before expiry) or when an API returns **401**.
- Read `refresh_token` from `localStorage`; if missing, redirect to login.

```http
POST {GATEWAY_URL}/api/auth/api/v1/auth/refresh
Content-Type: application/json

{ "refresh_token": "<from localStorage>" }
```

- **200:** Replace tokens in localStorage:
  ```javascript
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  ```
- **401:** Invalid/expired refresh token → clear storage and redirect to login.

### 7. Authenticated requests

For every request that requires a logged-in user:

- Add header: `Authorization: Bearer <access_token>` (read from localStorage).
- If the response is **401**, try **Refresh** once; if refresh succeeds, retry the request with the new access token; if refresh fails, clear storage and redirect to login.

### 8. Logout

```http
POST {GATEWAY_URL}/api/auth/api/v1/auth/logout
Content-Type: application/json

{ "refresh_token": "<from localStorage>", "access_token": "<from localStorage>" }
```

- **204:** Success. Then clear storage and redirect to login:
  ```javascript
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  ```

### 9. Get user + roles for guards (optional)

Call **Validate** with the current access token to get `user_id`, `email`, `role` (primary), `roles` (array). Use for route guards and UI.

```http
POST {GATEWAY_URL}/api/auth/api/v1/auth/validate
Content-Type: application/json

{ "token": "<access_token>" }
```

- **200:** `{ "user_id": "...", "email": "...", "role": "admin", "roles": ["admin", "analyst"] }`  
  Store in app state/context and use e.g. `roles.includes('admin')` for guards.
- **401:** Token invalid or revoked → try refresh or redirect to login.

---

## Quick reference: localStorage

| Key | Value |
|-----|--------|
| `access_token` | JWT access token (send in `Authorization: Bearer ...`) |
| `refresh_token` | JWT refresh token (send in body for `/refresh` and `/logout`) |

Optional: store `expires_in` (seconds) when you receive it from login/refresh to schedule proactive refresh.

---

## Error handling summary

| Status | Meaning | Frontend action |
|--------|--------|------------------|
| 400 | Validation / bad request | Show validation message |
| 401 | Invalid/expired token | Try refresh once; if fail → logout and go to login |
| 403 | Forbidden (e.g. email not verified) | Handle by case (e.g. redirect to verify-email) |
| 409 | Conflict (e.g. email already registered) | Show message |
| 429 | Rate limit | Show “too many attempts” and retry later |
