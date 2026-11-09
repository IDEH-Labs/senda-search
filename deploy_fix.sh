#!/usr/bin/env bash
set -e

echo "=== [Senda Search Engine] Despliegue y Activación en Debian ==="

# 1. Actualizar el paquete senda desde GitHub con las plantillas y assets estáticos
echo "[1/5] Actualizando senda-search con assets UI..."
/opt/senda/venv/bin/pip install --force-reinstall --no-deps "git+https://github.com/IDEH-Labs/senda-search.git"

# 2. Configurar senda.service
echo "[2/5] Verificando /etc/systemd/system/senda.service..."
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

# 3. Permisos
echo "[3/5] Aplicando permisos a /var/lib/senda..."
mkdir -p /var/lib/senda/data
chown -R senda:senda /var/lib/senda

# 4. Iniciar servicio
echo "[4/5] Reiniciando servicio systemd senda..."
systemctl daemon-reload
systemctl enable --now senda
systemctl restart senda

sleep 2

# 5. Verificación
echo "[5/5] Estado y verificación en local:"
systemctl status senda --no-pager

echo ""
echo "=== Test de respuesta HTTP (puerto 8000) ==="
curl -sI http://127.0.0.1:8000/api/v1/health || true
echo ""
echo "=== ¡Listo! Senda está en producción en https://senda.ideh.top ==="
