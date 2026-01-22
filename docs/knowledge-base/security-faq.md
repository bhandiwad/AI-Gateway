# Security FAQ

Common questions about security and compliance in AI Gateway.

---

## Data Protection

### How is my data protected? {#data-protection}

AI Gateway implements multiple layers of protection:

- **Encryption in transit**: All API traffic uses HTTPS/TLS
- **Encryption at rest**: Database encryption for sensitive data
- **Password hashing**: bcrypt with configurable rounds
- **API key hashing**: Keys are hashed before storage
- **PII redaction**: Automatic detection and redaction in logs

### Does AI Gateway store my prompts?

By default, AI Gateway logs requests for audit purposes. You can configure:

- **Log retention period**: How long logs are kept
- **PII redaction**: Automatically redact sensitive data
- **Logging policy**: What gets logged per tenant

### Where is my data stored?

Data is stored in your PostgreSQL database. AI Gateway is self-hosted, so you control where your data resides.

---

## Authentication

### How are passwords stored?

Passwords are hashed using bcrypt with configurable salt rounds (default: 12). Plain text passwords are never stored.

### How do JWT tokens work?

- Tokens are signed with your `JWT_SECRET_KEY`
- Default expiration: 24 hours (configurable)
- Tokens contain: user ID, email, role, permissions
- Tokens are stateless (no server-side session)

### Is SSO supported?

Yes, AI Gateway supports OIDC/OAuth2 SSO with:
- Google Workspace
- Microsoft Entra ID (Azure AD)
- Okta
- Auth0
- Any OIDC-compliant provider

---

## API Security

### How are API keys secured?

- Keys are generated using cryptographically secure random
- Only the hash is stored in the database
- The full key is shown only once at creation
- Keys can have expiration dates
- Keys can be revoked instantly

### What rate limiting is available?

- Per-tenant rate limits
- Per-API-key rate limits
- Configurable requests per minute
- Token-based rate limiting

---

## Compliance

### Is AI Gateway GDPR compliant?

AI Gateway provides tools for GDPR compliance:

- Data export capabilities
- User deletion workflows
- Audit logging
- Data retention policies
- PII detection and redaction

Implementation of GDPR compliance depends on your deployment and configuration.

### Is AI Gateway SOC 2 compliant?

AI Gateway is designed with SOC 2 principles in mind:

- Audit logging
- Access controls (RBAC)
- Encryption
- Monitoring capabilities

Actual SOC 2 compliance depends on your overall infrastructure and processes.

### Is there BFSI compliance support?

Yes, AI Gateway includes BFSI-specific guardrails:

- Financial advice detection
- Confidential data protection
- Enhanced PII detection (account numbers, etc.)
- Compliance audit trails

---

## Vulnerability Reporting

### How do I report a security vulnerability?

Please report security vulnerabilities privately:

1. Email: security@your-org.com
2. Do NOT create public GitHub issues
3. Include: description, steps to reproduce, impact assessment
4. We aim to respond within 48 hours

### What is your security update policy?

- Critical vulnerabilities: Patch within 24-48 hours
- High severity: Patch within 1 week
- Medium/Low: Included in next release
- Security advisories published for critical issues
