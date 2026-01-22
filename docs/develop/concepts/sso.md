# SSO Integration

Integrate AI Gateway with enterprise identity providers using OIDC/OAuth2.

---

## Supported providers

| Provider | Type | Status |
|----------|------|--------|
| Google Workspace | OIDC | ✓ Supported |
| Microsoft Entra ID | OIDC | ✓ Supported |
| Okta | OIDC | ✓ Supported |
| Auth0 | OIDC | ✓ Supported |
| OneLogin | OIDC | ✓ Supported |
| Keycloak | OIDC | ✓ Supported |
| Any OIDC provider | OIDC | ✓ Supported |

---

## Quick setup

### 1. Discover provider configuration

```bash
curl -X POST http://localhost:8000/api/v1/admin/sso/discover \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"issuer_url": "https://accounts.google.com"}'
```

### 2. Create OAuth app in your IdP

Configure redirect URI:
```
https://your-gateway.com/api/v1/admin/auth/sso/callback
```

### 3. Configure in AI Gateway

```bash
curl -X POST http://localhost:8000/api/v1/admin/sso/config \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "provider_name": "google",
    "display_name": "Sign in with Google",
    "issuer_url": "https://accounts.google.com",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "enabled": true
  }'
```

---

## SSO flow

```
User clicks "Sign in with Google"
          │
          ▼
    ┌─────────────┐
    │ AI Gateway  │ → Generate auth URL
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   Google    │ → User authenticates
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ AI Gateway  │ → Exchange code for token
    └──────┬──────┘   → Create/update user
           │          → Return JWT
           ▼
      User logged in
```

---

## Provider configuration

=== "Google"

    ```json
    {
      "provider_name": "google",
      "issuer_url": "https://accounts.google.com",
      "client_id": "YOUR_ID.apps.googleusercontent.com",
      "client_secret": "YOUR_SECRET",
      "scopes": ["openid", "email", "profile"]
    }
    ```

=== "Microsoft"

    ```json
    {
      "provider_name": "microsoft",
      "issuer_url": "https://login.microsoftonline.com/TENANT_ID/v2.0",
      "client_id": "YOUR_APPLICATION_ID",
      "client_secret": "YOUR_SECRET",
      "scopes": ["openid", "email", "profile"]
    }
    ```

=== "Okta"

    ```json
    {
      "provider_name": "okta",
      "issuer_url": "https://YOUR_DOMAIN.okta.com",
      "client_id": "YOUR_CLIENT_ID",
      "client_secret": "YOUR_SECRET",
      "scopes": ["openid", "email", "profile"]
    }
    ```

---

## User provisioning

### Auto-creation

New users are automatically created on first SSO login:

```json
{
  "auto_create_users": true,
  "default_role": "user"
}
```

### Role mapping

Map IdP groups to AI Gateway roles:

```json
{
  "role_mapping": {
    "gateway-admins": "admin",
    "gateway-users": "user"
  }
}
```

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/auth/sso/providers` | List providers |
| `POST` | `/admin/sso/discover` | OIDC discovery |
| `POST` | `/admin/sso/config` | Create provider |
| `POST` | `/admin/auth/sso/initiate` | Start SSO flow |
| `GET` | `/admin/auth/sso/callback` | Handle callback |

---

## Security

!!! warning "HTTPS required"
    SSO requires HTTPS for callback URLs in production.

!!! tip "Restrict domains"
    For Google/Microsoft, restrict to specific email domains:
    ```json
    {"allowed_domains": ["yourcompany.com"]}
    ```

