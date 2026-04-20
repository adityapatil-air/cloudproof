#!/bin/bash
set -e

# Stop existing app if running
if systemctl is-active --quiet cloudproof; then
    systemctl stop cloudproof
fi

# Install system dependencies if not present
if ! command -v python3 &>/dev/null; then
    apt-get update -y
    apt-get install -y python3 python3-pip
fi

if ! command -v nginx &>/dev/null; then
    apt-get update -y
    apt-get install -y nginx
fi
