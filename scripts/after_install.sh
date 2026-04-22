#!/bin/bash

echo "Starting AfterInstall..."

# ---------------- SYSTEM SETUP ----------------
apt-get update -y
apt-get install -y python3-dev build-essential python3.12-venv \
                   postgresql-client-16 netcat-openbsd nginx \
                   certbot python3-certbot-nginx

cd /home/ubuntu/backend

# ---------------- VENV ----------------
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt psycopg2-binary python-dotenv

# ---------------- FETCH DB HOST FROM SSM ----------------
echo "Fetching DB_HOST from SSM..."
for i in {1..20}; do
    DB_HOST=$(aws ssm get-parameter \
      --name /cloudproof/DB_HOST \
      --region ap-south-1 \
      --query Parameter.Value \
      --output text 2>/dev/null || echo "")
    if [ -n "$DB_HOST" ] && [ "$DB_HOST" != "None" ]; then
        echo "DB_HOST fetched: $DB_HOST"
        break
    fi
    echo "Waiting for DB_HOST in SSM... ($i/20)"
    sleep 15
done

# ---------------- FETCH DB SECRET ----------------
echo "Fetching DB credentials from Secrets Manager..."
SECRET=$(aws secretsmanager get-secret-value \
  --region ap-south-1 \
  --secret-id cloudproof-db-secret \
  --query SecretString \
  --output text)

DB_USER=$(echo $SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['username'])")
DB_PASSWORD=$(echo $SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['password'])")
DB_NAME=$(echo $SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['dbname'])")

export PGPASSWORD=$DB_PASSWORD

# ---------------- GENERATE .env FROM SSM ----------------
SECRET_KEY=$(aws ssm get-parameter \
  --name /cloudproof/SECRET_KEY \
  --region ap-south-1 \
  --query Parameter.Value \
  --output text 2>/dev/null || echo "change-this-to-a-random-secret")

cat > /home/ubuntu/backend/.env <<ENVEOF
DB_ENGINE=postgres
DB_HOST=$DB_HOST
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
SECRET_KEY=$SECRET_KEY
FRONTEND_URL=https://handsoncloud.in
ENVEOF

# ---------------- WAIT FOR RDS ----------------
echo "Waiting for RDS..."
for i in {1..20}; do
    nc -z $DB_HOST 5432 && break
    echo "DB not ready... retrying ($i/20)"
    sleep 5
done

# ---------------- CREATE DATABASE ----------------
echo "Creating database if not exists..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" || true

# ---------------- RUN SCHEMA ----------------
echo "Running schema.sql..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f /home/ubuntu/backend/schema.sql || true

echo "Database setup complete ✅"

# ---------------- PERMISSIONS ----------------
touch /home/ubuntu/backend/cloudproof.db
chown -R ubuntu:ubuntu /home/ubuntu/backend
chmod 664 /home/ubuntu/backend/cloudproof.db

# ---------------- NGINX HTTP CONFIG ----------------
cat > /etc/nginx/sites-available/cloudproof <<EOF
server {
    listen 80;
    server_name handsoncloud.in www.handsoncloud.in;

    location / {
        root /var/www/html;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;

        if (\$request_method = OPTIONS) {
            add_header Access-Control-Allow-Origin \$http_origin;
            add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
            add_header Access-Control-Allow-Headers 'Content-Type, Authorization';
            add_header Access-Control-Allow-Credentials 'true';
            return 204;
        }
    }
}
EOF

ln -sf /etc/nginx/sites-available/cloudproof /etc/nginx/sites-enabled/cloudproof
rm -f /etc/nginx/sites-enabled/default

systemctl restart nginx

# ---------------- HTTPS SETUP ----------------
echo "Setting up HTTPS with Certbot..."
certbot --nginx \
  -d handsoncloud.in \
  --non-interactive \
  --agree-tos \
  -m rjrohan0340@gmail.com \
  --redirect || echo "Certbot failed - run manually after DNS propagates"

# ---------------- AUTO RENEW ----------------
echo "0 3 * * * certbot renew --quiet" | crontab -

# ---------------- SYSTEMD SERVICE ----------------
cat > /etc/systemd/system/cloudproof.service <<EOF
[Unit]
Description=CloudProof Flask Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
ExecStart=/home/ubuntu/backend/venv/bin/python /home/ubuntu/backend/app.py
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/backend/.env

[Install]
WantedBy=multi-user.target
EOF

# ---------------- START SERVICES ----------------
systemctl daemon-reload
systemctl enable cloudproof
systemctl restart cloudproof || systemctl start cloudproof
systemctl restart nginx

echo "Deployment completed successfully 🚀"
