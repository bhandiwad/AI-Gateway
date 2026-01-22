# 🔐 SSO Integration Guide

This guide covers setting up Single Sign-On (SSO) with AI Gateway using OIDC/OAuth2 providers.

---

## Supported Providers

AI Gateway supports any OIDC-compliant identity provider:

| Provider | Type | Status |
|----------|------|--------|
| Google Workspace | OIDC | Fully Supported |
| Microsoft Entra ID (Azure AD) | OIDC | Fully Supported |
| Okta | OIDC | Fully Supported |
| Auth0 | OIDC | Fully Supported |
| OneLogin | OIDC | Fully Supported |
| Keycloak | OIDC | Fully Supported |
| Custom OIDC | OIDC | Supported |

---

## Prerequisites

Before configuring SSO, you need:

1. **Admin access** to your identity provider
2. **Admin account** on AI Gateway
3. **HTTPS enabled** on your AI Gateway deployment (required for OAuth callbacks)

---

## Configuration Steps

### Step 1: Discover OIDC Configuration

Use the discovery endpoint to fetch provider configuration:

```bash
curl -X POST http://localhost:8000/api/v1/admin/sso/discover \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"issuer_url": "https://accounts.google.com"}'
```

**Response:**
```json
{
  "issuer_url": "https://accounts.google.com",
  "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
  "token_endpoint": "https://oauth2.googleapis.com/token",
  "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
  "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
  "scopes_supported": ["openid", "email", "profile"]
}
```

### Step 2: Create OAuth Application

Configure an OAuth application in your identity provider.

#### Google Workspace

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. Select **Web application**
6. Add authorized redirect URI: `https://your-gateway.com/api/v1/admin/auth/sso/callback`
7. Save **Client ID** and **Client Secret**

#### Microsoft Entra ID

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID** → **App registrations**
3. Click **New registration**
4. Configure:
   - Name: AI Gateway
   - Supported account types: Single tenant (or multi-tenant)
   - Redirect URI: `https://your-gateway.com/api/v1/admin/auth/sso/callback`
5. Note the **Application (client) ID**
6. Go to **Certificates & secrets** → **New client secret**
7. Save the secret value

#### Okta

1. Log in to Okta Admin Console
2. Navigate to **Applications** → **Create App Integration**
3. Select **OIDC - OpenID Connect** and **Web Application**
4. Configure:
   - App name: AI Gateway
   - Sign-in redirect URIs: `https://your-gateway.com/api/v1/admin/auth/sso/callback`
   - Sign-out redirect URIs: `https://your-gateway.com/logout`
5. Save **Client ID** and **Client secret**

### Step 3: Configure SSO in AI Gateway

Create SSO configuration via API:

```bash
curl -X POST http://localhost:8000/api/v1/admin/sso/config \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "google",
    "display_name": "Sign in with Google",
    "issuer_url": "https://accounts.google.com",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "scopes": ["openid", "email", "profile"],
    "enabled": true,
    "auto_create_users": true,
    "default_role": "user"
  }'
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider_name` | string | Yes | Unique identifier (e.g., "google", "okta") |
| `display_name` | string | Yes | Button text for login page |
| `issuer_url` | string | Yes | OIDC issuer URL |
| `client_id` | string | Yes | OAuth client ID |
| `client_secret` | string | Yes | OAuth client secret |
| `scopes` | array | No | OAuth scopes (default: openid, email, profile) |
| `enabled` | boolean | No | Enable/disable provider (default: true) |
| `auto_create_users` | boolean | No | Auto-provision users (default: true) |
| `default_role` | string | No | Role for new users (default: "user") |

### Step 4: Test SSO Flow

1. List configured providers:
```bash
curl http://localhost:8000/api/v1/admin/auth/sso/providers
```

2. Initiate login:
```bash
curl -X POST http://localhost:8000/api/v1/admin/auth/sso/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "google",
    "redirect_uri": "https://your-gateway.com/dashboard"
  }'
```

3. The response includes `authorization_url` - redirect users there
4. After authentication, users are redirected to your callback with tokens

---

## SSO Flow Diagram

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  User   │────▶│  AI Gateway │────▶│   Identity   │────▶│   Gateway   │
│ Browser │     │   Frontend  │     │   Provider   │     │   Backend   │
└────┬────┘     └──────┬──────┘     └──────┬───────┘     └──────┬──────┘
     │                 │                   │                    │
     │  1. Click SSO   │                   │                    │
     │────────────────▶│                   │                    │
     │                 │                   │                    │
     │                 │ 2. Get Auth URL   │                    │
     │                 │──────────────────────────────────────▶│
     │                 │                   │                    │
     │                 │ 3. Return URL     │                    │
     │                 │◀──────────────────────────────────────│
     │                 │                   │                    │
     │  4. Redirect    │                   │                    │
     │◀────────────────│                   │                    │
     │                 │                   │                    │
     │  5. Login at IdP                    │                    │
     │────────────────────────────────────▶│                    │
     │                 │                   │                    │
     │  6. Callback with code              │                    │
     │◀────────────────────────────────────│                    │
     │                 │                   │                    │
     │  7. Exchange code                   │                    │
     │────────────────────────────────────────────────────────▶│
     │                 │                   │                    │
     │                 │                   │  8. Get tokens     │
     │                 │                   │◀───────────────────│
     │                 │                   │                    │
     │                 │                   │  9. Validate       │
     │                 │                   │───────────────────▶│
     │                 │                   │                    │
     │  10. Return JWT │                   │                    │
     │◀────────────────────────────────────────────────────────│
     │                 │                   │                    │
```

---

## Provider-Specific Configuration

### Google Workspace

```json
{
  "provider_name": "google",
  "display_name": "Sign in with Google",
  "issuer_url": "https://accounts.google.com",
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "YOUR_CLIENT_SECRET",
  "scopes": ["openid", "email", "profile"],
  "enabled": true
}
```

**Domain Restriction (G Suite):**
```json
{
  "allowed_domains": ["yourcompany.com"]
}
```

### Microsoft Entra ID

```json
{
  "provider_name": "microsoft",
  "display_name": "Sign in with Microsoft",
  "issuer_url": "https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0",
  "client_id": "YOUR_APPLICATION_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "scopes": ["openid", "email", "profile"],
  "enabled": true
}
```

**Multi-Tenant:**
```
issuer_url: https://login.microsoftonline.com/common/v2.0
```

### Okta

```json
{
  "provider_name": "okta",
  "display_name": "Sign in with Okta",
  "issuer_url": "https://YOUR_DOMAIN.okta.com",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "scopes": ["openid", "email", "profile"],
  "enabled": true
}
```

### Auth0

```json
{
  "provider_name": "auth0",
  "display_name": "Sign in with Auth0",
  "issuer_url": "https://YOUR_DOMAIN.auth0.com",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "scopes": ["openid", "email", "profile"],
  "enabled": true
}
```

---

## User Provisioning

### Auto-Creation

When `auto_create_users: true`, users are automatically created on first SSO login:

```json
{
  "auto_create_users": true,
  "default_role": "user",
  "default_tenant_id": null
}
```

### Just-In-Time (JIT) Provisioning

Map identity provider attributes to AI Gateway fields:

```json
{
  "attribute_mapping": {
    "email": "email",
    "name": "name",
    "given_name": "first_name",
    "family_name": "last_name",
    "groups": "roles"
  }
}
```

### Role Mapping

Map IdP groups to AI Gateway roles:

```json
{
  "role_mapping": {
    "gateway-admins": "admin",
    "gateway-users": "user",
    "gateway-viewers": "viewer"
  }
}
```

---

## Security Best Practices

### 1. Use HTTPS

SSO requires HTTPS for callback URLs. Configure SSL:

```bash
# In production nginx config
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
}
```

### 2. Validate State Parameter

AI Gateway automatically validates the OAuth state parameter to prevent CSRF attacks.

### 3. Secure Client Secrets

Store client secrets securely:

```bash
# Use environment variables
export SSO_GOOGLE_CLIENT_SECRET=your-secret

# Or secrets manager
aws secretsmanager get-secret-value --secret-id ai-gateway/sso
```

### 4. Restrict Allowed Domains

For Google/Microsoft, restrict to specific domains:

```json
{
  "allowed_domains": ["yourcompany.com", "subsidiary.com"]
}
```

### 5. Enable MFA at IdP

Require multi-factor authentication at your identity provider level.

---

## Troubleshooting

### Invalid Redirect URI

**Error:** `redirect_uri_mismatch`

**Solution:** Ensure the callback URL in your IdP exactly matches:
```
https://your-gateway.com/api/v1/admin/auth/sso/callback
```

### Token Exchange Failed

**Error:** `invalid_grant`

**Causes:**
- Authorization code expired (use within 10 minutes)
- Code already used
- Client credentials mismatch

### User Not Provisioned

**Error:** `User not found and auto-creation disabled`

**Solution:** Enable auto-creation or pre-provision users:
```json
{
  "auto_create_users": true
}
```

### CORS Issues

If frontend SSO redirect fails, check CORS:
```env
CORS_ORIGINS=https://your-frontend.com
```

---

## API Reference

### List Providers
```http
GET /api/v1/admin/auth/sso/providers
```

### Create Provider
```http
POST /api/v1/admin/sso/config
Authorization: Bearer ADMIN_TOKEN
```

### Update Provider
```http
PATCH /api/v1/admin/sso/config/{provider_name}
Authorization: Bearer ADMIN_TOKEN
```

### Delete Provider
```http
DELETE /api/v1/admin/sso/config/{provider_name}
Authorization: Bearer ADMIN_TOKEN
```

### Initiate Login
```http
POST /api/v1/admin/auth/sso/initiate
```

### Handle Callback
```http
GET /api/v1/admin/auth/sso/callback?code=...&state=...&provider_name=...
```

