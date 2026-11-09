#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>
# Senda Sovereign Search Engine — Production Automated Setup Script

set -euo pipefail

echo "=========================================================="
echo " Senda Sovereign Search Engine — Production Setup"
echo "=========================================================="

if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be executed as root (or with sudo)."
  exit 1
fi

# 1. Create dedicated system user and group
if ! id "senda" &>/dev/null; then
    echo "Creating system user 'senda'..."
    useradd -r -s /bin/false -d /var/lib/senda -m senda
else
    echo "User 'senda' already exists."
fi

# 2. Prepare directories and permissions
echo "Configuring directories..."
mkdir -p /var/lib/senda/data
mkdir -p /etc/senda
mkdir -p /opt/senda

chown -R senda:senda /var/lib/senda
chmod 750 /var/lib/senda

# 3. Copy ethical seeds catalog
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing ethical seeds catalog into /etc/senda/ethical_seeds.txt..."
cp "$REPO_DIR/seeds/ethical_seeds.txt" /etc/senda/ethical_seeds.txt
chown senda:senda /etc/senda/ethical_seeds.txt
chmod 644 /etc/senda/ethical_seeds.txt

# 4. Set up Python virtual environment
echo "Setting up Python virtual environment in /opt/senda/venv..."
python3 -m venv /opt/senda/venv
/opt/senda/venv/bin/pip install --upgrade pip
/opt/senda/venv/bin/pip install "$REPO_DIR"

ln -sf /opt/senda/venv/bin/senda /usr/local/bin/senda
chown -R senda:senda /opt/senda

# 5. Detect Init System (OpenRC vs Systemd)
if [ -d "/run/systemd/system" ]; then
    echo "Detected systemd init system."
    cp "$SCRIPT_DIR/systemd/senda.service" /etc/systemd/system/senda.service
    cp "$SCRIPT_DIR/systemd/senda-crawler.service" /etc/systemd/system/senda-crawler.service
    cp "$SCRIPT_DIR/systemd/senda-crawler.timer" /etc/systemd/system/senda-crawler.timer
    systemctl daemon-reload
    systemctl enable senda.service
    systemctl enable senda-crawler.timer
    echo "Systemd units installed and enabled."
elif [ -f "/sbin/openrc" ] || [ -f "/sbin/rc-service" ]; then
    echo "Detected Gentoo OpenRC init system."
    cp "$SCRIPT_DIR/openrc/senda" /etc/init.d/senda
    cp "$SCRIPT_DIR/openrc/senda.conf" /etc/conf.d/senda
    chmod +x /etc/init.d/senda
    rc-update add senda default
    echo "OpenRC service installed and added to default runlevel."
fi

# 6. Install Cron Maintenance Job (if cron directory exists)
if [ -d "/etc/cron.d" ]; then
    cp "$SCRIPT_DIR/cron/senda-crawler.cron" /etc/cron.d/senda-crawler
    chmod 644 /etc/cron.d/senda-crawler
    echo "Cron maintenance job installed."
fi

echo ""
echo "=========================================================="
echo " Installation Complete!"
echo "=========================================================="
echo ""
echo "Next steps on your production server:"
echo "1. Acquire TLS certificate for your domain:"
echo "   certbot certonly --standalone -d senda.ideh.top"
echo ""
echo "2. Copy Nginx configuration:"
echo "   cp $SCRIPT_DIR/nginx/senda.conf /etc/nginx/sites-available/senda.conf"
echo "   ln -sf /etc/nginx/sites-available/senda.conf /etc/nginx/sites-enabled/"
echo "   nginx -t && systemctl reload nginx (or rc-service nginx reload)"
echo ""
echo "3. Start Senda daemon:"
if [ -d "/run/systemd/system" ]; then
    echo "   systemctl start senda"
    echo "   systemctl start senda-crawler.timer"
else
    echo "   rc-service senda start"
fi
echo ""
echo "Your sovereign search engine is ready to serve the world!"
