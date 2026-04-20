#!/bin/bash
set -e

apt-get update -y
apt-get install -y python3-dev build-essential

cd /home/ubuntu/backend
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Safe .env copy
if [ ! -f /home/ubuntu/backend/.env ]; then
    if [ -f /home/ubuntu/backend/.env.example ]; then
        cp /home/ubuntu/backend/.env.example /home/ubuntu/backend/.env
    fi
fi

# Nginx config
cat > /etc/nginx/sites-available/cloudproof <<EOF
server {
    listen 80;
    server_name _;

    location / {
        root /var/www/html;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cloudproof /etc/nginx/sites-enabled/cloudproof
rm -f /etc/nginx/sites-enabled/default

# systemd service
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

systemctl daemon-reload
systemctl enable cloudproof
systemctl restart cloudproof || systemctl start cloudproof
systemctl restart nginx