#!/bin/bash
set -e

# Install Python dependencies
cd /home/ubuntu/backend
pip3 install -r requirements.txt

# Copy .env if not already present
if [ ! -f /home/ubuntu/backend/.env ]; then
    cp /home/ubuntu/backend/.env.example /home/ubuntu/backend/.env
fi

# Configure nginx to serve frontend and proxy backend
cat > /etc/nginx/sites-available/cloudproof <<EOF
server {
    listen 80;

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

# Create systemd service for Flask backend
cat > /etc/systemd/system/cloudproof.service <<EOF
[Unit]
Description=CloudProof Flask Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/backend/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cloudproof
