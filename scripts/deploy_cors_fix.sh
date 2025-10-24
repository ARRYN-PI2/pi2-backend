#!/bin/bash

# ============================================
# Script de Despliegue - Fix CORS
# ============================================

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
BACKEND_IP="3.133.11.109"
EC2_USER="ec2-user"
PROJECT_PATH="/home/ec2-user/arryn-backend"
SSH_KEY_PATH="${SSH_KEY_PATH:-~/.ssh/arryn-backend.pem}"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DESPLIEGUE DE FIX CORS - ARRYN      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Verificar si existe la llave SSH
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}⚠️  Llave SSH no encontrada en: $SSH_KEY_PATH${NC}"
    echo -e "${YELLOW}   Por favor, especifica la ruta correcta:${NC}"
    read -p "   Ruta de la llave SSH: " SSH_KEY_PATH
    
    if [ ! -f "$SSH_KEY_PATH" ]; then
        echo -e "${RED}❌ Error: Llave SSH no encontrada${NC}"
        exit 1
    fi
fi

# Verificar permisos de la llave
chmod 400 "$SSH_KEY_PATH" 2>/dev/null

echo -e "${GREEN}✓${NC} Llave SSH encontrada: $SSH_KEY_PATH"
echo ""

# Función para ejecutar comandos en EC2
run_remote() {
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "${EC2_USER}@${BACKEND_IP}" "$@"
}

# Función para copiar archivos a EC2
copy_to_remote() {
    scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$@"
}

echo -e "${BLUE}[1/6]${NC} Verificando conexión con EC2..."
if run_remote "echo 'Conexión exitosa'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Conectado a EC2: ${BACKEND_IP}"
else
    echo -e "${RED}❌ Error: No se pudo conectar a EC2${NC}"
    echo -e "${YELLOW}   Verifica:${NC}"
    echo -e "${YELLOW}   1. La IP del servidor: ${BACKEND_IP}${NC}"
    echo -e "${YELLOW}   2. La llave SSH tenga permisos 400${NC}"
    echo -e "${YELLOW}   3. Los Security Groups permitan SSH desde tu IP${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[2/6]${NC} Haciendo backup del archivo .env.prod actual..."
run_remote "cd ${PROJECT_PATH} && cp .env.prod .env.prod.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"
echo -e "${GREEN}✓${NC} Backup creado"
echo ""

echo -e "${BLUE}[3/6]${NC} Copiando nuevo archivo .env.prod al servidor..."
copy_to_remote .env.prod "${EC2_USER}@${BACKEND_IP}:${PROJECT_PATH}/.env.prod"
echo -e "${GREEN}✓${NC} Archivo copiado"
echo ""

echo -e "${BLUE}[4/6]${NC} Verificando configuración CORS en el servidor..."
CORS_CONFIG=$(run_remote "grep CORS_ALLOWED_ORIGINS ${PROJECT_PATH}/.env.prod")
echo -e "${GREEN}✓${NC} Configuración CORS:"
echo "   ${CORS_CONFIG}"
echo ""

echo -e "${BLUE}[5/6]${NC} Reiniciando servicios Docker..."
run_remote "cd ${PROJECT_PATH} && docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d"
echo -e "${GREEN}✓${NC} Servicios reiniciados"
echo ""

echo -e "${BLUE}[6/6]${NC} Esperando que los servicios estén listos..."
sleep 5

# Verificar que el backend esté respondiendo
echo "Probando backend..."
if curl -s --connect-timeout 10 http://${BACKEND_IP}:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend está respondiendo"
else
    echo -e "${YELLOW}⚠️  Backend no responde en /api/health (puede ser normal si no existe ese endpoint)${NC}"
fi
echo ""

# Probar CORS
echo "Probando CORS desde https://arryn.app..."
CORS_TEST=$(curl -s -I -X OPTIONS http://${BACKEND_IP}:8000/api/products/ \
  -H "Origin: https://arryn.app" \
  -H "Access-Control-Request-Method: GET" 2>&1 | grep -i "access-control" || echo "")

if [ -n "$CORS_TEST" ]; then
    echo -e "${GREEN}✓${NC} CORS configurado correctamente:"
    echo "$CORS_TEST" | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  No se detectaron headers CORS en la respuesta${NC}"
    echo -e "${YELLOW}   Verifica los logs del contenedor:${NC}"
    echo -e "${YELLOW}   ssh -i $SSH_KEY_PATH ${EC2_USER}@${BACKEND_IP}${NC}"
    echo -e "${YELLOW}   cd ${PROJECT_PATH} && docker-compose -f docker-compose.prod.yml logs arryn-backend${NC}"
fi
echo ""

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         DESPLIEGUE COMPLETADO          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📝 Próximos pasos:${NC}"
echo ""
echo "1. Abre tu frontend: https://arryn.app"
echo "2. Abre la consola del navegador (F12)"
echo "3. Intenta hacer una petición al backend"
echo "4. Si aún hay errores, revisa los logs:"
echo ""
echo -e "${YELLOW}   ssh -i $SSH_KEY_PATH ${EC2_USER}@${BACKEND_IP}${NC}"
echo -e "${YELLOW}   cd ${PROJECT_PATH}${NC}"
echo -e "${YELLOW}   docker-compose -f docker-compose.prod.yml logs -f arryn-backend${NC}"
echo ""
echo -e "${BLUE}🔧 Para revertir cambios:${NC}"
echo -e "${YELLOW}   ssh -i $SSH_KEY_PATH ${EC2_USER}@${BACKEND_IP}${NC}"
echo -e "${YELLOW}   cd ${PROJECT_PATH}${NC}"
echo -e "${YELLOW}   cp .env.prod.backup.* .env.prod${NC}"
echo -e "${YELLOW}   docker-compose -f docker-compose.prod.yml restart${NC}"
echo ""
