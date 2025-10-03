# 🎯 ARRYN Backend - Sistema de Comparación de Precios

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2.5-green.svg)
![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Sistema avanzado de comparación de precios con algoritmos de ranking inteligente, análisis de tendencias y reportes empresariales. Diseñado para alta concurrencia y escalabilidad.

## 🚀 Características Principales

### 🎯 **Funcionalidades Core**
- **🏆 Mejores precios personalizados** - Recomendaciones basadas en preferencias de usuario
- **📊 Ranking inteligente de ofertas** - Algoritmos avanzados que combinan precio y frescura
- **📈 Análisis de tendencias** - Identificación de productos en tendencia
- **🏪 Comparación entre tiendas** - Análisis comparativo con métricas empresariales
- **📋 Reportes avanzados** - Estadísticas y análisis de mercado

### ⚡ **Performance y Escalabilidad**
- **🛡️ Rate limiting** - Control de tráfico por IP (100 req/min configurable)
- **🚀 Cache inteligente** - Respuestas optimizadas con TTL de 5 minutos
- **📝 Logging avanzado** - Monitoreo completo de performance
- **🐳 Docker Ready** - Contenedorización completa con Docker Compose
- **🔧 Alta concurrencia** - Middleware personalizado para manejo de carga

### 🗄️ **Arquitectura Robusta**
- **🏗️ Arquitectura Hexagonal** - Clean Architecture implementada
- **🍃 MongoDB + Fallback** - Base de datos NoSQL con sistema de respaldo
- **🔒 Configuración por variables** - Ambiente flexible con .env
- **🧪 Testing Ready** - Estructura preparada para tests

## 📋 Tabla de Contenidos

- [🛠️ Instalación](#%EF%B8%8F-instalación)
- [🐳 Docker](#-docker)
- [🌐 API Endpoints](#-api-endpoints)
- [📊 Ejemplos de Uso](#-ejemplos-de-uso)
- [🔧 Configuración](#-configuración)
- [🏗️ Arquitectura](#%EF%B8%8F-arquitectura)
- [🧪 Testing](#-testing)
- [📈 Monitoreo](#-monitoreo)
- [🤝 Contribución](#-contribución)

## 🛠️ Instalación

### Prerrequisitos
- Python 3.13+
- MongoDB (opcional, tiene fallback)
- Docker y Docker Compose (recomendado)

### 🚀 Instalación Rápida con Docker

```bash
# 1. Clonar repositorio
git clone https://github.com/ARRYN-PI2/pi2-backend.git
cd pi2-backend

# 2. Configuración inicial
make dev-setup

# 3. ¡Listo! 🎉
# Backend: http://localhost:8000
# MongoDB: mongodb://localhost:27017
```

### 📦 Instalación Manual

```bash
# 1. Clonar y configurar entorno
git clone https://github.com/ARRYN-PI2/pi2-backend.git
cd pi2-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env.dev

# 4. Migraciones y servidor
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## 🐳 Docker

### Desarrollo
```bash
# Construir y levantar servicios
make build && make up

# Ver logs en tiempo real
make logs

# Acceder al shell del contenedor
make shell

# Ejecutar migraciones
make migrate
```

### Producción
```bash
# Configurar variables de producción
cp .env.example .env.prod
# Editar .env.prod con valores de producción

# Levantar en producción
make prod-up

# Monitorear
make prod-logs
```

### Comandos Útiles de Docker
```bash
make help          # Ver todos los comandos disponibles
make status         # Estado de servicios
make health         # Verificar salud del sistema
make clean          # Limpiar contenedores no utilizados
make security-scan  # Escanear vulnerabilidades
```

## 🌐 API Endpoints

### 🎯 **Comparación de Precios**
```http
GET /api/best-prices/{category}/?user_id=123&limit=10
GET /api/price-comparison/?product=iPhone&category=electronics
```

### 🏆 **Ranking y Tendencias**
```http
GET /api/ranked-offers/?category=electronics&limit=20
GET /api/trending-offers/?days=7&limit=15
```

### 📊 **Reportes Empresariales**
```http
GET /api/reports/store-comparison/?category=electronics&days=30
GET /api/reports/price-analysis/{category}/?days=30
```

### 👥 **Gestión de Usuarios**
```http
GET /api/user/                 # Listar usuarios
POST /api/user/create          # Crear usuario
GET /api/user/{id}/            # Usuario específico
```

### 📁 **Gestión de Datos**
```http
POST /api/archivos/            # Subir datos JSON
GET /api/archivos/             # Obtener datos
GET /api/brands/               # Listar marcas disponibles
```

## 📊 Ejemplos de Uso

### 🎯 Obtener Mejores Precios
```bash
curl -X GET "http://localhost:8000/api/best-prices/electronics/?user_id=1&limit=5" \
  -H "Accept: application/json"
```

**Respuesta:**
```json
{
  "category": "electronics",
  "user_id": "1", 
  "personalized": true,
  "count": 5,
  "results": [
    {
      "_id": "64f...",
      "titulo": "iPhone 15 Pro",
      "marca": "APPLE",
      "precio_valor": 999,
      "precio_texto": "$999",
      "ahorro_estimado": 50,
      "categoria": "electronics"
    }
  ]
}
```

### 🏆 Ranking de Ofertas
```bash
curl -X GET "http://localhost:8000/api/ranked-offers/?category=electronics&limit=3" \
  -H "Accept: application/json"
```

**Respuesta:**
```json
{
  "category": "electronics",
  "ranking_algorithm": "value_score",
  "count": 3,
  "results": [
    {
      "_id": "64f...",
      "titulo": "MacBook Air M3",
      "score_total": 0.95,
      "score_precio": 0.90,
      "score_freshness": 1.0,
      "percentil_precio": 10
    }
  ]
}
```

### 📈 Ofertas Trending
```bash
curl -X GET "http://localhost:8000/api/trending-offers/?limit=3" \
  -H "Accept: application/json"
```

### 📊 Reportes de Tiendas
```bash
curl -X GET "http://localhost:8000/api/reports/store-comparison/?period_days=30" \
  -H "Accept: application/json"
```

## 🔧 Configuración

### 🔒 Seguridad: SECRET_KEY

**⚠️ IMPORTANTE:** El `SECRET_KEY` es obligatorio y debe ser único para cada entorno.

#### Generar SECRET_KEY
```bash
# Opción 1: Usando Django (recomendado)
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Opción 2: Usando Python estándar
python -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)') for _ in range(50)))"
```

#### Configurar SECRET_KEY
```bash
# Desarrollo (.env.dev)
SECRET_KEY=tu-clave-generada-para-desarrollo

# Producción (usar gestor de secretos o variables de entorno)
export SECRET_KEY="tu-clave-generada-para-produccion"
```

**⚠️ Buenas Prácticas:**
- ✅ Generar una clave única para cada entorno (dev, staging, production)
- ✅ Nunca compartir el SECRET_KEY entre ambientes
- ✅ Usar gestores de secretos en producción (AWS Secrets Manager, Azure Key Vault, etc.)
- ✅ Rotar el SECRET_KEY periódicamente
- ❌ NUNCA commitear el SECRET_KEY real al repositorio
- ❌ NUNCA usar el mismo SECRET_KEY en desarrollo y producción

### Variables de Entorno (.env)

```bash
# Django
DEBUG=True
SECRET_KEY=GENERAR-CON-COMANDO-ARRIBA
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=arryn_products_db

# Performance
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
CACHE_TIMEOUT=300

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Configuraciones de Performance

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `RATE_LIMIT_REQUESTS` | Requests por minuto por IP | 100 |
| `CACHE_TIMEOUT` | Tiempo de cache en segundos | 300 |
| `REQUEST_LOG_SLOW_THRESHOLD` | Umbral para requests lentos | 1.0s |
| `GUNICORN_WORKERS` | Workers de Gunicorn | 3 |

## 🏗️ Arquitectura

### 📁 Estructura del Proyecto
```
pi2-backend/
├── 🐳 Docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── docker-entrypoint.sh
├── 🏗️ Arryn_Back/
│   ├── 💼 domain/              # Lógica de negocio
│   │   ├── models/
│   │   └── services/
│   │       ├── mongo_service.py     # Gestión MongoDB
│   │       ├── price_service.py     # Lógica de precios
│   │       ├── ranking_service.py   # Algoritmos de ranking
│   │       └── report_service.py    # Generación de reportes
│   ├── 🎯 application/         # Casos de uso
│   │   ├── interfaces/
│   │   └── use_cases/
│   └── 🔧 infrastructure/      # Implementación técnica
│       ├── api/                     # API REST
│       ├── config/                  # Configuración Django
│       └── middleware/              # Middleware personalizado
├── 📊 scripts/                # Scripts de utilidad
├── 🧪 tests/                  # Tests unitarios
└── 📋 Archivos de configuración
```

### 🛡️ Middleware Stack

1. **CORS Middleware** - Manejo de CORS
2. **Rate Limit Middleware** - Control de tráfico  
3. **Response Cache Middleware** - Cache inteligente
4. **Request Logging Middleware** - Logging de performance
5. **Django Security Stack** - Seguridad estándar

## 🧪 Testing

```bash
# Tests con Docker
make test

# Tests con coverage
make test-coverage

# Tests manuales
python manage.py test

# Tests específicos
python manage.py test Arryn_Back.tests.test_api
```

### Estructura de Tests
```bash
tests/
├── infrastructure/
│   ├── test_api.py         # Tests de API
│   ├── test_middleware.py  # Tests de middleware
│   └── test_views.py       # Tests de vistas
├── domain/
│   ├── test_services.py    # Tests de servicios
│   └── test_models.py      # Tests de modelos
└── integration/
    └── test_workflows.py   # Tests de integración
```

## 📈 Monitoreo

### 📊 Métricas Disponibles
- **Performance**: Tiempo de respuesta, throughput
- **Errores**: Rate de errores, tipos de error
- **Cache**: Hit rate, miss rate
- **Rate Limiting**: Requests bloqueados, IPs afectadas

### 📝 Logs
```bash
# Ver logs en tiempo real
make logs

# Logs específicos del backend
make logs-backend

# Archivo de logs
tail -f django.log
```

### 🔍 Health Checks
```bash
# Verificar salud del sistema
make health

# Health check manual
curl -f http://localhost:8000/api/brands/
```

## 🤝 Contribución

### 📋 Proceso de Contribución

1. **Fork** el repositorio
2. **Crear rama** para tu feature
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Desarrollar** con tests
4. **Commit** siguiendo convenciones
   ```bash
   git commit -m "feat: agregar nueva funcionalidad de ranking"
   ```
5. **Push** y crear **Pull Request**

### 📝 Convenciones de Commit
- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Documentación
- `style:` Formato de código
- `refactor:` Refactorización
- `test:` Tests
- `chore:` Mantenimiento

### 🧪 Checklist de PR
- [ ] Tests pasando
- [ ] Cobertura de tests mantenida
- [ ] Documentación actualizada
- [ ] Variables de entorno documentadas
- [ ] Docker build exitoso

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **Django Team** por el excelente framework
- **MongoDB** por la base de datos NoSQL
- **Docker** por la contenedorización
- **Comunidad Open Source** por las herramientas

---

<div align="center">

**🚀 ARRYN Team - Comparación Inteligente de Precios**

[![GitHub](https://img.shields.io/badge/GitHub-ARRYN--PI2-blue?style=flat&logo=github)](https://github.com/ARRYN-PI2)
[![Docker](https://img.shields.io/badge/Docker-Hub-blue?style=flat&logo=docker)](https://hub.docker.com)

*Construido con ❤️ para revolucionar la comparación de precios*

</div>