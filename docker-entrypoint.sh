#!/bin/bash
set -e

# Función de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Función para esperar por MongoDB (opcional)
wait_for_mongo() {
    if [ -n "$MONGO_HOST" ] && [ -n "$MONGO_PORT" ]; then
        log "Esperando a MongoDB en $MONGO_HOST:$MONGO_PORT..."
        while ! nc -z "$MONGO_HOST" "$MONGO_PORT"; do
            sleep 1
        done
        log "✅ MongoDB está disponible"
    fi
}

# Función para ejecutar migraciones
run_migrations() {
    log "Ejecutando migraciones de base de datos..."
    python manage.py makemigrations --noinput
    python manage.py migrate --noinput
    log "✅ Migraciones completadas"
}

# Función para recopilar archivos estáticos
collect_static() {
    log "Recopilando archivos estáticos..."
    python manage.py collectstatic --noinput --clear
    log "✅ Archivos estáticos recopilados"
}

# Función para crear superusuario
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log "Creando superusuario..."
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print("Superusuario creado exitosamente")
else:
    print("Superusuario ya existe")
EOF
        log "✅ Superusuario configurado"
    fi
}

# Función principal
main() {
    log "🚀 Iniciando Arryn Backend..."
    
    # Configurar variables de entorno por defecto
    export DEBUG=${DEBUG:-False}
    export ALLOWED_HOSTS=${ALLOWED_HOSTS:-"localhost,127.0.0.1,0.0.0.0"}
    
    case "$1" in
        "gunicorn")
            log "Modo: Producción con Gunicorn"
            wait_for_mongo
            run_migrations
            collect_static
            create_superuser
            
            log "🌟 Iniciando servidor Gunicorn..."
            exec gunicorn \
                --bind 0.0.0.0:8000 \
                --workers ${GUNICORN_WORKERS:-3} \
                --worker-class ${GUNICORN_WORKER_CLASS:-sync} \
                --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
                --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
                --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
                --timeout ${GUNICORN_TIMEOUT:-30} \
                --keep-alive ${GUNICORN_KEEP_ALIVE:-5} \
                --log-level ${GUNICORN_LOG_LEVEL:-info} \
                --access-logfile - \
                --error-logfile - \
                Arryn_Back.infrastructure.config.wsgi:application
            ;;
        
        "development"|"dev")
            log "Modo: Desarrollo con Django runserver"
            export DEBUG=True
            wait_for_mongo
            run_migrations
            
            log "🔧 Iniciando servidor de desarrollo..."
            exec python manage.py runserver 0.0.0.0:8000
            ;;
        
        "shell")
            log "Modo: Shell interactivo"
            wait_for_mongo
            run_migrations
            exec python manage.py shell
            ;;
        
        "migrate")
            log "Modo: Solo migraciones"
            wait_for_mongo
            run_migrations
            log "✅ Migraciones completadas. Saliendo..."
            ;;
        
        "test")
            log "Modo: Ejecutar tests"
            wait_for_mongo
            run_migrations
            log "🧪 Ejecutando tests..."
            exec python manage.py test
            ;;
        
        *)
            log "Modo: Comando personalizado"
            wait_for_mongo
            run_migrations
            exec "$@"
            ;;
    esac
}

# Ejecutar función principal
main "$@"