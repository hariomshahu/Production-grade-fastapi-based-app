#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

# Add swap so npm build doesn't OOM on t3.micro (1GB RAM)
fallback_swap=/swapfile
if [ ! -f "$fallback_swap" ]; then
  dd if=/dev/zero of="$fallback_swap" bs=1M count=1024
  chmod 600 "$fallback_swap"
  mkswap "$fallback_swap"
  swapon "$fallback_swap"
  echo "$fallback_swap none swap sw 0 0" >> /etc/fstab
fi

# Install Nginx, Python, Git, Node (for building frontend)
apt-get update
apt-get install -y nginx python3-pip python3-venv git curl

# Node 20 (for Vite build)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# App directory
APP_DIR=/opt/app
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Clone repo (must be public or use SSH key)
git clone --depth 1 -b "${branch}" "${repo_url}" repo
cd repo

# Apply Nginx config early so we don't serve default "Welcome to nginx"
cp terraform/nginx-app.conf /etc/nginx/conf.d/app.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl start nginx

# Backend venv and deps
cd "$APP_DIR/repo/backend"
python3 -m venv venv
. venv/bin/activate
pip install --no-cache-dir -r requirements.txt
cd "$APP_DIR/repo"

# Frontend build (swap helps avoid OOM)
cd frontend
npm ci
npm run build
mkdir -p /var/www/app
cp -r dist/* /var/www/app/
cd "$APP_DIR/repo"

# Reload nginx in case we need to pick up new static files
systemctl reload nginx

# Run FastAPI with Gunicorn (bind to 127.0.0.1 only)
# Pass DYNAMODB_TABLE explicitly so it is set for the gunicorn process (nohup can drop env)
cd "$APP_DIR/repo/backend"
. venv/bin/activate
export BIND_HOST=127.0.0.1
export DYNAMODB_TABLE="${table_name}"

# Use env so the variable is visible to gunicorn and its workers (region + table for boto3)
nohup env BIND_HOST=127.0.0.1 AWS_DEFAULT_REGION="${aws_region}" DYNAMODB_TABLE="${table_name}" gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 app.main:app > /var/log/app.log 2>&1 &
echo $! > /var/run/app.pid
