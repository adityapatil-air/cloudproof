#!/bin/bash
set -e

# Start Flask backend
systemctl start cloudproof

# Restart nginx to pick up any config changes
systemctl restart nginx
