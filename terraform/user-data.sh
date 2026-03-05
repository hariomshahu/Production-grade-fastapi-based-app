#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

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

# Backend venv and deps
cd backend
python3 -m venv venv
. venv/bin/activate
pip install --no-cache-dir -r requirements.txt
cd ..

# Frontend build
cd frontend
npm ci
npm run build
mkdir -p /var/www/app
cp -r dist/* /var/www/app/
cd ..

# Nginx config
cp terraform/nginx-app.conf /etc/nginx/conf.d/app.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl start nginx

# Run FastAPI with Gunicorn (bind to 127.0.0.1 only)
cd "$APP_DIR/repo/backend"
. venv/bin/activate
export BIND_HOST=127.0.0.1
export DYNAMODB_TABLE="${table_name}"

# Run in background; use systemd for production-grade process management
nohup gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 app.main:app > /var/log/app.log 2>&1 &
echo $! > /var/run/app.pid
