#!/bin/bash

# ============================================
# Script para solucionar problema de CORS
# ============================================

echo "🔍 DIAGNÓSTICO DE CONFIGURACIÓN AWS"
echo "===================================="
echo ""

# Información encontrada
CLOUDFRONT_URL="https://d2objaapejmkqm.cloudfront.net"
DOMAIN_1="https://arryn.app"
DOMAIN_2="https://www.arryn.app"
BACKEND_IP="3.133.11.109"

echo "✅ Frontend CloudFront: $CLOUDFRONT_URL"
echo "✅ Dominio principal: $DOMAIN_1"
echo "✅ Dominio alternativo: $DOMAIN_2"
echo "✅ Backend IP: $BACKEND_IP"
echo ""

# Verificar archivo .env.prod
echo "📝 Verificando configuración en .env.prod..."
if grep -q "arryn.app" .env.prod; then
    echo "✅ CORS_ALLOWED_ORIGINS actualizado correctamente"
else
    echo "❌ ERROR: CORS_ALLOWED_ORIGINS NO está actualizado"
    echo "   Ejecuta: sed -i '' 's|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=https://arryn.app,https://www.arryn.app,https://d2objaapejmkqm.cloudfront.net|g' .env.prod"
fi
echo ""

# Verificar si el backend está corriendo
echo "🔌 Verificando backend en EC2..."
if curl -s --connect-timeout 5 http://${BACKEND_IP}:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend está respondiendo"
else
    echo "⚠️  Backend no responde en http://${BACKEND_IP}:8000"
    echo "   ¿Está el servicio Docker corriendo en EC2?"
fi
echo ""

# Pasos siguientes
echo "📋 PASOS SIGUIENTES PARA SOLUCIONAR EL PROBLEMA:"
echo "================================================"
echo ""
echo "1️⃣  ACTUALIZAR VARIABLES DE ENTORNO EN EC2"
echo "   SSH a tu servidor:"
echo "   ssh -i tu-key.pem ec2-user@${BACKEND_IP}"
echo ""
echo "   Luego actualiza el archivo .env.prod:"
echo "   nano /home/ec2-user/arryn-backend/.env.prod"
echo ""
echo "   Asegúrate de que tenga:"
echo "   CORS_ALLOWED_ORIGINS=https://arryn.app,https://www.arryn.app,https://d2objaapejmkqm.cloudfront.net"
echo ""
echo "2️⃣  REINICIAR EL SERVICIO DOCKER"
echo "   cd /home/ec2-user/arryn-backend"
echo "   docker-compose -f docker-compose.prod.yml down"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "3️⃣  VERIFICAR LOGS"
echo "   docker-compose -f docker-compose.prod.yml logs -f arryn-backend"
echo ""
echo "4️⃣  PROBAR DESDE EL FRONTEND"
echo "   Abre: $DOMAIN_1"
echo "   Verifica la consola del navegador (F12)"
echo ""
echo "============================================"
echo "💡 CHECKLIST DE SEGURIDAD S3/CLOUDFRONT"
echo "============================================"
echo ""
echo "[ ] Bucket S3 permite acceso público (solo lectura)"
echo "[ ] CloudFront está configurado con HTTPS"
echo "[ ] Certificado SSL válido en CloudFront"
echo "[ ] Backend permite CORS desde frontend"
echo "[ ] Security Groups de EC2 permiten tráfico en puerto 8000"
echo ""
