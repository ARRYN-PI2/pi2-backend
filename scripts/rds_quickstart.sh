#!/bin/bash
# =================================
# Script de Quick Start para AWS RDS
# =================================
# Este script automatiza la configuración inicial

set -e  # Salir si hay errores

echo "========================================="
echo "🚀 ARRYN BACKEND - AWS RDS QUICK START"
echo "========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

print_success "Directorio del proyecto encontrado"

# Paso 1: Verificar archivo .env
echo ""
echo "========================================="
echo "📝 Paso 1: Verificar configuración"
echo "========================================="

if [ ! -f ".env.prod" ]; then
    print_warning "Archivo .env.prod no encontrado"
    
    if [ -f ".env.rds.example" ]; then
        read -p "¿Copiar .env.rds.example a .env.prod? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.rds.example .env.prod
            print_success "Archivo .env.prod creado"
            print_warning "IMPORTANTE: Edita .env.prod con tus credenciales de AWS RDS"
            read -p "Presiona Enter cuando hayas configurado .env.prod..."
        else
            print_error "Necesitas crear el archivo .env.prod antes de continuar"
            exit 1
        fi
    else
        print_error "No se encontró .env.rds.example. Descarga el repositorio completo."
        exit 1
    fi
else
    print_success "Archivo .env.prod encontrado"
fi

# Paso 2: Verificar dependencias
echo ""
echo "========================================="
echo "📦 Paso 2: Instalar dependencias"
echo "========================================="

if [ -d ".venv" ]; then
    print_info "Activando entorno virtual..."
    source .venv/bin/activate
    print_success "Entorno virtual activado"
else
    print_warning "No se encontró .venv"
    read -p "¿Crear entorno virtual? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 -m venv .venv
        source .venv/bin/activate
        print_success "Entorno virtual creado y activado"
    fi
fi

print_info "Instalando/actualizando dependencias..."
pip install -r requirements.txt --quiet
print_success "Dependencias instaladas"

# Paso 3: Validar conexión
echo ""
echo "========================================="
echo "🔌 Paso 3: Validar conexión a RDS"
echo "========================================="

if [ -f "scripts/validate_rds_connection.py" ]; then
    python scripts/validate_rds_connection.py
    
    if [ $? -ne 0 ]; then
        print_error "La validación de conexión falló"
        print_info "Revisa los errores anteriores y corrige tu configuración"
        exit 1
    fi
else
    print_warning "Script de validación no encontrado, continuando..."
fi

# Paso 4: Ejecutar migraciones
echo ""
echo "========================================="
echo "🔄 Paso 4: Ejecutar migraciones"
echo "========================================="

read -p "¿Ejecutar migraciones ahora? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Verificando migraciones..."
    python manage.py showmigrations
    
    echo ""
    print_info "Aplicando migraciones..."
    python manage.py migrate
    
    if [ $? -eq 0 ]; then
        print_success "Migraciones aplicadas exitosamente"
    else
        print_error "Error al aplicar migraciones"
        exit 1
    fi
fi

# Paso 5: Crear superusuario
echo ""
echo "========================================="
echo "👤 Paso 5: Crear superusuario"
echo "========================================="

read -p "¿Crear superusuario ahora? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Creando superusuario..."
    python manage.py createsuperuser
    
    if [ $? -eq 0 ]; then
        print_success "Superusuario creado exitosamente"
    else
        print_warning "No se pudo crear el superusuario (puede que ya exista)"
    fi
fi

# Paso 6: Recolectar archivos estáticos
echo ""
echo "========================================="
echo "📁 Paso 6: Archivos estáticos"
echo "========================================="

read -p "¿Recolectar archivos estáticos? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
    
    if [ $? -eq 0 ]; then
        print_success "Archivos estáticos recolectados"
    else
        print_warning "Error al recolectar archivos estáticos"
    fi
fi

# Resumen final
echo ""
echo "========================================="
echo "🎉 ¡CONFIGURACIÓN COMPLETADA!"
echo "========================================="
echo ""
print_success "El backend está configurado y listo para usar"
echo ""
echo "Próximos pasos:"
echo "  1. Iniciar servidor de desarrollo:"
echo "     python manage.py runserver"
echo ""
echo "  2. O desplegar con Docker:"
echo "     docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "  3. Acceder al panel de administración:"
echo "     http://localhost:8000/admin/"
echo ""
echo "Para más información, consulta:"
echo "  📖 AWS_RDS_DEPLOYMENT_GUIDE.md"
echo ""
