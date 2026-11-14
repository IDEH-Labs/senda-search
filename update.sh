#!/usr/bin/env bash
set -e

# Asegurar privilegios de root
if [ "$EUID" -ne 0 ]; then
    echo "Este script requiere permisos de superusuario (root)."
    echo "Por favor ejecútalo como: curl -sSL https://codeberg.org/IDEH-Labs/senda-search/raw/branch/main/update.sh | sudo bash"
    exit 1
fi

echo "=== [Senda Search Engine] Actualización Soberana de Senda ==="

# 1. Localizar o crear el entorno virtual
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

echo "Entorno detectado: $VENV_DIR"

# Asegurar disponibilidad de pip
if ! "$PYTHON_EXEC" -m pip --version &>/dev/null; then
    echo "Instalando pip en el entorno..."
    "$PYTHON_EXEC" -m ensurepip --upgrade 2>/dev/null || (apt-get update && apt-get install -y python3-pip python3-venv git && python3 -m venv --upgrade "$VENV_DIR")
fi

# 2. Instalar dependencias fijadas y versión de Senda
SENDA_TARGET_REF="${1:-${SENDA_TARGET_REF:-main}}"
echo "[1/4] Verificando e instalando dependencias desde lockfile..."
curl -sSL "https://codeberg.org/IDEH-Labs/senda-search/raw/branch/main/requirements-lock.txt" -o /tmp/requirements-lock.txt 2>/dev/null || true
if [ -s /tmp/requirements-lock.txt ]; then
    "$PYTHON_EXEC" -m pip install --no-cache-dir -r /tmp/requirements-lock.txt
fi

echo "[2/4] Instalando la versión de Senda (Ref: $SENDA_TARGET_REF)..."
if ! "$PYTHON_EXEC" -m pip install --no-cache-dir --force-reinstall --no-deps "git+https://codeberg.org/IDEH-Labs/senda-search.git@$SENDA_TARGET_REF"; then
    echo "Fallo en Codeberg, intentando con GitHub..."
    if ! "$PYTHON_EXEC" -m pip install --no-cache-dir --force-reinstall --no-deps "git+https://github.com/IDEH-Labs/senda-search.git@$SENDA_TARGET_REF"; then
        echo "Fallo en GitHub, intentando con GitLab..."
        "$PYTHON_EXEC" -m pip install --no-cache-dir --force-reinstall --no-deps "git+https://gitlab.com/ideh-labs/senda-search.git@$SENDA_TARGET_REF"
    fi
fi

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
EnvironmentFile=-/etc/senda/senda.env
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

# 4. Directorio de datos y permisos
echo "[3/4] Ajustando permisos de almacenamiento..."
mkdir -p /var/lib/senda/data
id -u senda &>/dev/null || useradd -r -s /bin/false -d /var/lib/senda senda
chown -R senda:senda /var/lib/senda /opt/senda 2>/dev/null || true

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
echo "=== ¡Listo! Senda Minimalista está activo en https://senda.ideh.top ==="
