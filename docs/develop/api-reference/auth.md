# Authentication API

Endpoints for user registration, login, and session management.

---

## Register {#register}

Create a new tenant account.

```http
POST /api/v1/admin/auth/register
```

**Request:**
```json
{
  "name": "Your Name",
  "email": "you@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "tenant": {
    "id": 1,
    "name": "Your Name",
    "email": "you@example.com",
    "is_active": true,
    "is_admin": false
  }
}
```

---

## Login {#login}

Authenticate and receive an access token.

```http
POST /api/v1/admin/auth/login
```

**Request:**
```json
{
  "email": "you@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "tenant": {
    "id": 1,
    "name": "Your Name",
    "email": "you@example.com"
  }
}
```

---

## Current User {#current-user}

Get the currently authenticated user.

```http
GET /api/v1/admin/auth/me
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Your Name",
  "email": "you@example.com",
  "is_admin": false
}
```

---

## SSO {#sso}

### List SSO Providers

```http
GET /api/v1/admin/auth/sso/providers
```

### Initiate SSO Login

```http
POST /api/v1/admin/auth/sso/initiate
```

**Request:**
```json
{
  "provider_name": "google",
  "redirect_uri": "https://your-app.com/callback"
}
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-string"
}
```

### SSO Callback

```http
GET /api/v1/admin/auth/sso/callback?code=AUTH_CODE&state=STATE&provider_name=google
```
