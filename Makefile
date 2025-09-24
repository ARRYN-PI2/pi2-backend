# Makefile para Arryn Backend
.PHONY: help build up down logs shell test clean

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yml
SERVICE_NAME = arryn-backend

# Comandos principales
help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construir las imágenes Docker
	$(DOCKER_COMPOSE) build

build-prod: ## Construir las imágenes para producción
	$(DOCKER_COMPOSE_PROD) build

up: ## Levantar servicios en desarrollo
	$(DOCKER_COMPOSE) up -d

up-logs: ## Levantar servicios y mostrar logs
	$(DOCKER_COMPOSE) up

down: ## Detener todos los servicios
	$(DOCKER_COMPOSE) down

down-prod: ## Detener servicios de producción
	$(DOCKER_COMPOSE_PROD) down

restart: ## Reiniciar servicios
	$(DOCKER_COMPOSE) restart

logs: ## Ver logs de todos los servicios
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Ver logs solo del backend
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

shell: ## Acceder al shell del contenedor backend
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) bash

django-shell: ## Acceder al shell de Django
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py shell

migrate: ## Ejecutar migraciones
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py migrate

makemigrations: ## Crear nuevas migraciones
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py makemigrations

collectstatic: ## Recopilar archivos estáticos
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py collectstatic --noinput

createsuperuser: ## Crear superusuario
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py createsuperuser

test: ## Ejecutar tests
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py test

test-coverage: ## Ejecutar tests con cobertura
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) coverage run --source='.' manage.py test
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) coverage report

clean: ## Limpiar contenedores, imágenes y volúmenes no utilizados
	docker system prune -af
	docker volume prune -f

clean-all: ## Limpiar todo incluyendo volúmenes de datos
	$(DOCKER_COMPOSE) down -v
	docker system prune -af
	docker volume prune -f

# Comandos de producción
prod-up: ## Levantar servicios en producción
	$(DOCKER_COMPOSE_PROD) up -d

prod-logs: ## Ver logs de producción
	$(DOCKER_COMPOSE_PROD) logs -f

prod-shell: ## Shell en producción
	$(DOCKER_COMPOSE_PROD) exec $(SERVICE_NAME) bash

prod-migrate: ## Migraciones en producción
	$(DOCKER_COMPOSE_PROD) exec $(SERVICE_NAME) python manage.py migrate

# Comandos de base de datos
db-backup: ## Hacer backup de MongoDB
	docker exec arryn-mongodb-prod mongodump --archive=/data/backup/$(shell date +%Y%m%d_%H%M%S).archive --gzip

db-restore: ## Restaurar MongoDB (especificar BACKUP_FILE=filename)
	docker exec arryn-mongodb-prod mongorestore --archive=/data/backup/$(BACKUP_FILE) --gzip

# Comandos de desarrollo
dev-setup: ## Configuración inicial para desarrollo
	cp .env.example .env.dev
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up -d
	sleep 10
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py migrate
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python manage.py collectstatic --noinput
	@echo "🎉 Configuración de desarrollo completada!"
	@echo "🌐 Backend disponible en: http://localhost:8000"
	@echo "📊 MongoDB disponible en: mongodb://localhost:27017"

# Comandos de monitoreo
status: ## Ver estado de los servicios
	$(DOCKER_COMPOSE) ps

stats: ## Ver uso de recursos
	docker stats

health: ## Verificar salud de los servicios
	curl -f http://localhost:8000/api/brands/ || echo "❌ Backend no está respondiendo"
	docker exec arryn-mongodb mongo --eval "db.admin.runCommand('ping')" || echo "❌ MongoDB no está respondiendo"

# Comandos de seguridad
security-scan: ## Escanear vulnerabilidades en las imágenes
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image arryn-backend

# Información del sistema
info: ## Mostrar información del sistema
	@echo "🐳 Docker version:"
	@docker --version
	@echo "🐙 Docker Compose version:"
	@docker-compose --version
	@echo "📊 System info:"
	@docker system df