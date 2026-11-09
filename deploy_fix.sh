#!/usr/bin/env bash
set -e

echo "=== [Senda Search Engine] Configurando servicio en Debian ==="

# 1. Configurar senda.service de forma limpia
cat << 'EOF' > /etc/systemd/system/senda.service
[Unit]
Description=Senda Search Engine Daemon
After=network.target

[Service]
Type=simple
User=senda
Group=senda
WorkingDirectory=/var/lib/senda
Environment="SENDA_DATABASE_PATH=/var/lib/senda/data/senda.db"
Environment="SENDA_HOST=127.0.0.1"
Environment="SENDA_PORT=8000"
Environment="SENDA_ENVIRONMENT=production"
ExecStart=/opt/senda/venv/bin/senda serve --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 2. Eliminar referencias problemáticas a .env en el código instalado
find /opt/senda/venv -name "config.py" -exec sed -i '/env_file/d' {} + 2>/dev/null || true

# 3. Directorio de datos y permisos
mkdir -p /var/lib/senda/data
chown -R senda:senda /var/lib/senda

# 4. Recargar systemd e iniciar senda
systemctl daemon-reload
systemctl enable --now senda
systemctl restart senda

sleep 2

# 5. Diagnóstico de estado
echo "=== Estado de senda.service ==="
systemctl status senda --no-pager

echo ""
echo "=== Verificando puerto 8000 ==="
curl -sI http://127.0.0.1:8000/api/v1/health || true
echo ""
echo "=== ¡Listo! Senda está en línea ==="
