#!/usr/bin/env bash
set -e

echo "=== [Senda Search Engine] Actualización de Interfaz Minimalista ==="

# 1. Localizar o restaurar el entorno virtual
VENV_DIR="/opt/senda/venv"
if [ ! -d "$VENV_DIR" ]; then
    if [ -d "/var/lib/senda/.venv" ]; then
        VENV_DIR="/var/lib/senda/.venv"
    else
        mkdir -p /opt/senda
        python3 -m venv /opt/senda/venv
        VENV_DIR="/opt/senda/venv"
    fi
fi

PYTHON_EXEC="$VENV_DIR/bin/python3"
if [ ! -x "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="$VENV_DIR/bin/python"
fi

echo "Entorno detectado: $VENV_DIR (Python: $PYTHON_EXEC)"

# Asegurar disponibilidad de pip
if ! "$PYTHON_EXEC" -m pip --version &>/dev/null; then
    echo "Restaurando pip en el entorno..."
    "$PYTHON_EXEC" -m ensurepip --upgrade 2>/dev/null || (apt-get update && apt-get install -y python3-pip python3-venv && python3 -m venv --upgrade "$VENV_DIR")
fi

# 2. Instalar la última versión de Senda desde GitHub
echo "[1/4] Instalando la versión minimalista de Senda..."
"$PYTHON_EXEC" -m pip install --no-cache-dir --force-reinstall --no-deps "git+https://github.com/IDEH-Labs/senda-search.git"

# 3. Configurar senda.service
echo "[2/4] Verificando servicio systemd..."
cat << EOF > /etc/systemd/system/senda.service
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
ExecStart=$VENV_DIR/bin/senda serve --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 4. Permisos
echo "[3/4] Ajustando permisos de almacenamiento..."
mkdir -p /var/lib/senda/data
chown -R senda:senda /var/lib/senda

# 5. Reiniciar servicio
echo "[4/4] Reiniciando Senda..."
systemctl daemon-reload
systemctl enable --now senda
systemctl restart senda

sleep 2

# Verificación
echo "=== Estado del servicio ==="
systemctl status senda --no-pager

echo ""
echo "=== Test de respuesta local ==="
curl -sI http://127.0.0.1:8000/api/v1/health || true
echo ""
echo "=== ¡Listo! Senda está actualizado en https://senda.ideh.top ==="
