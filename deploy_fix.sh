#!/usr/bin/env bash
set -e

echo "=== [Senda Search Engine] Despliegue y Activación en Debian ==="

# 1. Actualizar dependencias y el paquete senda desde GitHub
echo "[1/5] Actualizando uvicorn y senda-search..."
/opt/senda/venv/bin/pip install --upgrade --force-reinstall "uvicorn[standard]"
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
echo "[5/5] Logs y diagnóstico del fallo:"
journalctl -u senda -n 30 --no-pager

echo ""
echo "=== Test directo de importación como usuario senda ==="
su -s /bin/bash senda -c "cd /var/lib/senda && /opt/senda/venv/bin/python3 -c 'from senda.api.app import app; print(\"APP OK\")'" || true

echo ""
echo "=== Test de respuesta HTTP (puerto 8000) ==="
curl -sI http://127.0.0.1:8000/api/v1/health || true
echo ""
echo "=== Fin del script de diagnóstico ==="
