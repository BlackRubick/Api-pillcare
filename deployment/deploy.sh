#!/bin/bash

# Script de despliegue para PillCare 360 desde repositorio clonado
# Ejecutar desde: sudo bash /opt/pillcare360/app/deployment/deploy.sh

set -e

echo "🚀 Desplegando PillCare 360 desde repositorio"
echo "============================================="

# Variables
APP_USER="pillcare360"
APP_DIR="/opt/pillcare360"
REPO_DIR="${APP_DIR}/app"
VENV_DIR="${APP_DIR}/venv"
SERVICE_NAME="pillcare360"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verificar root
if [[ $EUID -ne 0 ]]; then
   log_error "Ejecutar como root: sudo bash deploy.sh"
   exit 1
fi

# Verificar que existe el repositorio clonado
if [ ! -d "${REPO_DIR}" ] || [ ! -f "${REPO_DIR}/app/main.py" ]; then
    log_error "No se encontró el código clonado en ${REPO_DIR}"
    log_error "Primero clona tu repositorio:"
    log_error "cd ${APP_DIR} && sudo -u ${APP_USER} git clone TU_REPO app"
    exit 1
fi

log_info "Código fuente encontrado en ${REPO_DIR}"

# 1. Detener servicios existentes
log_info "Deteniendo servicios..."
systemctl stop ${SERVICE_NAME} 2>/dev/null || true

# 2. Actualizar repositorio
log_info "Actualizando código desde repositorio..."
cd ${REPO_DIR}
sudo -u ${APP_USER} git pull origin main || sudo -u ${APP_USER} git pull origin master

# 3. Crear/actualizar entorno virtual
log_info "Configurando entorno virtual..."
if [ -d "${VENV_DIR}" ]; then
    rm -rf "${VENV_DIR}"
fi

sudo -u ${APP_USER} python3.11 -m venv "${VENV_DIR}"
sudo -u ${APP_USER} "${VENV_DIR}/bin/pip" install --upgrade pip

# 4. Instalar dependencias
log_info "Instalando dependencias..."
if [ -f "${REPO_DIR}/requirements.txt" ]; then
    sudo -u ${APP_USER} "${VENV_DIR}/bin/pip" install -r "${REPO_DIR}/requirements.txt"
elif [ -f "${REPO_DIR}/pyproject.toml" ]; then
    sudo -u ${APP_USER} "${VENV_DIR}/bin/pip" install -e "${REPO_DIR}"
else
    log_warn "No se encontró requirements.txt, instalando dependencias básicas..."
    sudo -u ${APP_USER} "${VENV_DIR}/bin/pip" install \
        fastapi uvicorn sqlalchemy pymysql python-jose passlib \
        python-multipart pydantic pydantic-settings python-dotenv
fi

# 5. Crear enlaces simbólicos para configuración
log_info "Configurando archivos de configuración..."
if [ ! -f "${REPO_DIR}/.env" ]; then
    ln -sf "${APP_DIR}/.env" "${REPO_DIR}/.env"
fi

# 6. Crear/migrar base de datos
log_info "Configurando base de datos..."
cd ${REPO_DIR}
sudo -u ${APP_USER} env $(cat ${APP_DIR}/.env | grep -v '^#' | xargs) "${VENV_DIR}/bin/python" -c "
import sys
sys.path.append('.')
try:
    from app.core.database import create_tables, test_connection
    print('🔗 Probando conexión a MySQL...')
    if test_connection():
        print('✅ Conexión exitosa')
        print('🔨 Creando/verificando tablas...')
        create_tables()
        print('✅ Base de datos lista')
    else:
        print('❌ Error de conexión')
        sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

# 7. Crear servicio systemd
log_info "Configurando servicio systemd..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=PillCare 360 FastAPI Application
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=exec
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${REPO_DIR}
Environment=PATH=${VENV_DIR}/bin
EnvironmentFile=${APP_DIR}/.env
ExecStart=${VENV_DIR}/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

# Logging
StandardOutput=append:${APP_DIR}/logs/app.log
StandardError=append:${APP_DIR}/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# 8. Configurar Nginx
log_info "Configurando Nginx..."
cat > /etc/nginx/sites-available/pillcare360 << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    # Logs
    access_log /opt/pillcare360/logs/nginx_access.log;
    error_log /opt/pillcare360/logs/nginx_error.log;

    # API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # Archivos estáticos
    location /static/ {
        alias /opt/pillcare360/static/;
        expires 30d;
    }
}
EOF

# Activar sitio
ln -sf /etc/nginx/sites-available/pillcare360 /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# 9. Configurar permisos
log_info "Ajustando permisos..."
chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
chmod 600 ${APP_DIR}/.env

# 10. Crear script de actualización
cat > ${APP_DIR}/update.sh << 'EOF'
#!/bin/bash
# Script para actualizar PillCare 360

echo "🔄 Actualizando PillCare 360..."

# Ir al directorio del repo
cd /opt/pillcare360/app

# Hacer pull del código
sudo -u pillcare360 git pull

# Reiniciar el servicio
sudo systemctl restart pillcare360

echo "✅ Actualización completada"
sudo systemctl status pillcare360
EOF

chmod +x ${APP_DIR}/update.sh

# 11. Iniciar servicios
log_info "Iniciando servicios..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}
systemctl reload nginx

# 12. Verificar que todo funcione
sleep 5

echo ""
echo "🔍 VERIFICANDO SERVICIOS:"
echo "========================"

# Verificar servicios
if systemctl is-active --quiet ${SERVICE_NAME}; then
    log_info "✅ PillCare 360: CORRIENDO"
else
    log_error "❌ PillCare 360: FALLÓ"
    echo "Ver logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
fi

if systemctl is-active --quiet nginx; then
    log_info "✅ Nginx: CORRIENDO"
else
    log_error "❌ Nginx: FALLÓ"
fi

if systemctl is-active --quiet mysql; then
    log_info "✅ MySQL: CORRIENDO"
else
    log_error "❌ MySQL: FALLÓ"
fi

# Test de la API
log_info "Probando API..."
sleep 3
if curl -f -s http://localhost:8000/health > /dev/null; then
    log_info "✅ API respondiendo en puerto 8000"
else
    log_warn "⚠️ API no responde - revisar logs"
fi

# 13. Información final
echo ""
echo "🎉 ¡DESPLIEGUE COMPLETADO!"
echo "========================"
echo ""
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "TU_IP_PUBLICA")
echo "🌐 Tu API está disponible en:"
echo "   http://${PUBLIC_IP}/"
echo "   http://${PUBLIC_IP}/docs"
echo "   http://${PUBLIC_IP}/health"
echo ""
echo "📋 COMANDOS ÚTILES:"
echo "   Actualizar código:    sudo ${APP_DIR}/update.sh"
echo "   Ver logs:             sudo tail -f ${APP_DIR}/logs/app.log"
echo "   Ver errores:          sudo tail -f ${APP_DIR}/logs/error.log"
echo "   Reiniciar app:        sudo systemctl restart ${SERVICE_NAME}"
echo "   Estado de servicios:  sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "🔧 ARCHIVOS IMPORTANTES:"
echo "   Código:      ${REPO_DIR}/"
echo "   Config:      ${APP_DIR}/.env"
echo "   Logs:        ${APP_DIR}/logs/"
echo "   Actualizar:  ${APP_DIR}/update.sh"
echo ""