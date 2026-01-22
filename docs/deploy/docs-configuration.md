# Documentation Server Configuration

The InfinitAI Gateway includes built-in documentation that can be accessed in multiple ways.

---

## Access Options

| Option | URL | Best For |
|--------|-----|----------|
| **Path-based** (default) | `yourdomain.com/docs` | Simple setup, single domain |
| **Subdomain** | `docs.yourdomain.com` | Separate docs domain |
| **Standalone port** | `yourdomain.com:8080` | Development, testing |

---

## Option 1: Path-Based (Default)

Docs are served at `/docs` path via nginx proxy. This works out of the box.

**Access:** `http://localhost/docs`

**How it works:**

```
Request to /docs/*
       │
       ▼
    nginx (port 80)
       │
       ▼
  docs service (internal port 8000)
```

**docker-compose.yml** (default):
```yaml
docs:
  image: squidfunk/mkdocs-material:latest
  volumes:
    - ./docs:/docs/docs:ro
    - ./mkdocs.yml:/docs/mkdocs.yml:ro
  working_dir: /docs
  command: serve -a 0.0.0.0:8000
  restart: unless-stopped
```

**nginx.conf** includes:
```nginx
location /docs/ {
    proxy_pass http://docs:8000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}
```

---

## Option 2: Subdomain

Serve docs at a separate subdomain like `docs.yourdomain.com`.

### Setup

1. **Copy subdomain nginx config:**
   ```bash
   cp nginx.docs-subdomain.conf nginx.conf
   ```

2. **Rebuild and restart:**
   ```bash
   docker-compose build frontend
   docker-compose up -d
   ```

3. **Configure DNS:**
   Add a DNS record pointing `docs.yourdomain.com` to your server.

4. **Update mkdocs.yml:**
   ```yaml
   site_url: https://docs.yourdomain.com
   ```

**Access:** `http://docs.localhost` (local) or `http://docs.yourdomain.com`

---

## Option 3: Standalone Port

Expose docs on a separate port for development or if you don't want nginx proxying.

### Setup

1. **Edit docker-compose.yml:**
   ```yaml
   docs:
     image: squidfunk/mkdocs-material:latest
     ports:
       - "8080:8000"  # Uncomment this line
     volumes:
       - ./docs:/docs/docs:ro
       - ./mkdocs.yml:/docs/mkdocs.yml:ro
     working_dir: /docs
     command: serve -a 0.0.0.0:8000
   ```

2. **Restart:**
   ```bash
   docker-compose up -d docs
   ```

**Access:** `http://localhost:8080`

---

## Local Development (Without Docker)

Run docs locally for development:

```bash
# Install MkDocs Material
pip install mkdocs-material

# Serve docs with hot reload
mkdocs serve

# Access at http://127.0.0.1:8000
```

---

## Customization

### Change Site Name

Edit `mkdocs.yml`:
```yaml
site_name: Your Company Gateway
```

### Change Logo

Replace `docs/assets/logo.png` with your logo.

### Change Colors

Edit `docs/assets/extra.css`:
```css
:root {
  --md-primary-fg-color: #YOUR_COLOR;
  --md-accent-fg-color: #YOUR_ACCENT;
}
```

### Disable Docs

Remove or comment out the docs service in `docker-compose.yml` and the `/docs` location in `nginx.conf`.

---

## Production Considerations

### HTTPS

For production, configure SSL in nginx:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /docs/ {
        proxy_pass http://docs:8000/;
        # ... other proxy settings
    }
}
```

### Caching

Add caching headers for static docs assets:

```nginx
location /docs/ {
    proxy_pass http://docs:8000/;
    
    # Cache static assets
    location ~* \.(css|js|png|jpg|ico|svg)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```
