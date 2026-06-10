# Deploy — DigitalOcean Droplet

Guide to deploy World Cup Predictions on a DigitalOcean Droplet with Docker Compose.

## 1. Create the Droplet

- Image: **Ubuntu 24.04**
- Plan: **Basic $6/month** (1 vCPU, 1 GB RAM, 25 GB SSD) — enough for MVP
- Region: closest to your users (e.g., Frankfurt for Europe)
- Auth: **SSH key** (recommended)

## 2. Initial server setup

```bash
ssh root@YOUR_IP

# Update
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose plugin (if not included)
apt install -y docker-compose-plugin

# Create a deploy user (optional but recommended)
adduser deploy
usermod -aG docker deploy
```

## 3. Clone and configure

```bash
# As deploy user (or root)
cd /opt
git clone https://github.com/YOUR_USER/world-cup-predictions.git
cd world-cup-predictions

# Create production env
cp .env.prod.example .env.prod

# Edit with real values:
nano .env.prod
```

**Important: change these values in .env.prod:**
- `POSTGRES_PASSWORD` — strong random password
- `JWT_SECRET_KEY` — run: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `DOMAIN` — your domain or Droplet IP
- `CORS_ORIGINS` — `https://your-domain.com` or `http://YOUR_IP`
- `DEBUG` — must be `False`

## 4. Build and start

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check everything is running:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs api --tail 20
```

The app should be accessible at `http://YOUR_IP`.

## 5. Load data (first time)

```bash
# Run the pipeline inside the api container
docker compose -f docker-compose.prod.yml exec api \
  python -m pipelines.football_data.run --skip-squads
```

## 6. DNS and SSL (optional but recommended)

### Point your domain
Add an A record in your DNS provider:
```
A  @  YOUR_DROPLET_IP
```

### Get SSL certificate
```bash
# First, update server_name in deploy/nginx/default.conf to your domain

docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d your-domain.com \
  --email your@email.com \
  --agree-tos --no-eff-email
```

Then uncomment the HTTPS server block in `deploy/nginx/default.conf`, replace `YOUR_DOMAIN`, and restart nginx:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### Auto-renew (cron)
```bash
crontab -e
# Add:
0 5 1 */2 * docker compose -f /opt/world-cup-predictions/docker-compose.prod.yml run --rm certbot renew && docker compose -f /opt/world-cup-predictions/docker-compose.prod.yml restart nginx
```

## 7. Backups

```bash
# Manual backup
./deploy/scripts/backup-db.sh

# Automatic daily backup (cron)
crontab -e
# Add:
0 3 * * * /opt/world-cup-predictions/deploy/scripts/backup-db.sh >> /var/log/worldcup-backup.log 2>&1
```

## 8. Updates

```bash
cd /opt/world-cup-predictions
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Architecture

```
Internet
   │
   ▼
┌─────────┐
│  Nginx  │ :80 / :443
│ (proxy) │
└────┬────┘
     │
     ├── /api/*  ──► API (FastAPI) :8000
     │
     └── /*      ──► Frontend (React/Nginx) :80
                         │
                    PostgreSQL :5432
```
