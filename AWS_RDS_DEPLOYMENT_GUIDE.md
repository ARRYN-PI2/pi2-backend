# 📋 Guía de Configuración AWS RDS PostgreSQL para Arryn Backend

## 🎯 Objetivo
Configurar una instancia de Amazon RDS PostgreSQL y conectar la aplicación Django para migración de base de datos.

---

## 📦 Prerrequisitos

- [ ] Cuenta AWS con permisos para crear instancias RDS
- [ ] VPC y Security Groups configurados
- [ ] Acceso a AWS Console o AWS CLI
- [ ] Aplicación Django local funcionando

---

## 🚀 Paso 1: Crear Instancia RDS PostgreSQL en AWS

### 1.1 Acceder a RDS en AWS Console
1. Ir a **AWS Console** → **RDS** → **Databases**
2. Click en **"Create database"**

### 1.2 Configuración de la Instancia

**Método de Creación:**
- Seleccionar: **Standard create**

**Motor de Base de Datos:**
- Engine type: **PostgreSQL**
- Version: **PostgreSQL 17.x** (o version mayor disponible)



**Configuración de Credenciales:**
```
DB instance identifier: arryn-backend-db
Master username: arryn_admin
Master password: [GENERAR_PASSWORD_SEGURO]
```
> ⚠️ **IMPORTANTE**: Guarda el password en un gestor de secretos (AWS Secrets Manager o similar)

**Configuración de Instancia:**
- DB instance class: 
  - Free tier: `db.t3.micro` o `db.t4g.micro`
  - Producción: `db.t3.medium` o superior
- Storage type: **General Purpose SSD (gp3)**
- Allocated storage: **20 GB** (mínimo, ajustar según necesidad)

**Conectividad:**
- Virtual private cloud (VPC): [Seleccionar VPC existente]
- Public access: 
  - ✅ **Yes** (para testing inicial desde local)
  - ❌ **No** (para producción, usar VPN o bastion host)
- VPC security group: **Create new** o seleccionar existente
  - Security group name: `arryn-backend-db-sg`

**Configuración Adicional:**
- Initial database name: `arryn_db`
- DB parameter group: default
- Backup retention period: 7 días (mínimo recomendado)
- Enable encryption: ✅ (recomendado para producción)

### 1.3 Finalizar Creación
- Click en **"Create database"**
- Esperar ~10-15 minutos hasta que el estado sea **"Available"**

---

## 🔐 Paso 2: Configurar Security Group

### 2.1 Reglas de Entrada (Inbound Rules)

Ir a **EC2** → **Security Groups** → Buscar el security group de RDS

**Agregar regla:**
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: 
  - Para testing: 0.0.0.0/0 (cualquier IP) ⚠️ SOLO TEMPORAL
  - Para producción: [IP_DE_TU_SERVIDOR_BACKEND] o Security Group del backend
Description: PostgreSQL access for Arryn Backend
```

> ⚠️ **SEGURIDAD**: Nunca dejes `0.0.0.0/0` en producción. Usa la IP específica del servidor o el Security Group del backend.

---

## 📝 Paso 3: Obtener Credenciales de Conexión

### 3.1 Información del Endpoint

En **RDS Console** → **Databases** → Click en `arryn-backend-db`

**Copiar los siguientes datos:**
```
Endpoint: arryn-backend-db.xxxxxxxxx.us-east-1.rds.amazonaws.com
Port: 5432
Database name: arryn_db
Master username: arryn_admin
Master password: [EL_PASSWORD_QUE_CREASTE]
```

---

## ⚙️ Paso 4: Configurar Variables de Entorno

### 4.1 Crear/Actualizar archivo `.env.prod`

En el servidor de producción, crear/editar el archivo `.env.prod`:

```bash
# =================================
# AWS RDS PostgreSQL Configuration
# =================================

# Database Configuration (PostgreSQL)
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=arryn_db
DATABASE_USER=arryn_admin
DATABASE_PASSWORD=[TU_PASSWORD_SEGURO]
DATABASE_HOST=arryn-backend-db.xxxxxxxxx.us-east-1.rds.amazonaws.com
DATABASE_PORT=5432

# Django Configuration
DEBUG=False
SECRET_KEY=[GENERAR_NUEVO_SECRET_KEY]
ALLOWED_HOSTS=tu-dominio.com,*.amazonaws.com,tu-ip-elastica

# MongoDB Configuration (si aplica)
MONGO_HOST=
MONGO_PORT=
MONGO_DB_NAME=arryn_products_db
MONGODB_URL=[TU_MONGODB_ATLAS_URL_SI_APLICA]

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://tu-frontend.com,https://www.tu-frontend.com

# Cache Configuration
CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache
CACHE_LOCATION=arryn-cache
CACHE_TIMEOUT=300

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/arryn/django.log
```

### 4.2 Generar SECRET_KEY

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## 🧪 Paso 5: Probar Conexión Localmente

### 5.1 Instalar Dependencias

```bash
cd /ruta/al/proyecto/pi2-backend
pip install -r requirements.txt
```

### 5.2 Verificar Conexión

Crear archivo temporal `test_connection.py`:

```python
import psycopg2
import os

try:
    conn = psycopg2.connect(
        host="arryn-backend-db.xxxxxxxxx.us-east-1.rds.amazonaws.com",
        port=5432,
        database="arryn_db",
        user="arryn_admin",
        password="TU_PASSWORD",
        connect_timeout=10
    )
    print("✅ Conexión exitosa a RDS PostgreSQL")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"📊 Versión PostgreSQL: {db_version[0]}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error de conexión: {e}")
```

Ejecutar:
```bash
python test_connection.py
```

---

## 🔄 Paso 6: Ejecutar Migraciones

### 6.1 Verificar Configuración Django

```bash
# Verificar que Django detecta PostgreSQL
python manage.py check --database default
```

### 6.2 Crear Migraciones

```bash
# Crear migraciones si no existen
python manage.py makemigrations

# Verificar migraciones pendientes
python manage.py showmigrations
```

### 6.3 Aplicar Migraciones

```bash
# Aplicar todas las migraciones
python manage.py migrate

# Salida esperada:
# Operations to perform:
#   Apply all migrations: admin, api, auth, contenttypes, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
```

### 6.4 Verificar Tablas Creadas

```bash
# Conectarse a RDS
psql -h arryn-backend-db.xxxxxxxxx.us-east-1.rds.amazonaws.com \
     -U arryn_admin \
     -d arryn_db \
     -p 5432

# Dentro de psql:
\dt  # Listar todas las tablas
\d api_user  # Ver estructura de tabla específica
SELECT COUNT(*) FROM django_migrations;  # Contar migraciones aplicadas
\q  # Salir
```

---

## 👤 Paso 7: Crear Usuario Administrador

### 7.1 Crear Superusuario

```bash
python manage.py createsuperuser

# Ingresar:
# Username: admin
# Email: admin@arryn.com
# Password: [PASSWORD_SEGURO]
```

### 7.2 O usar variables de entorno (recomendado para automatización)

Agregar a `.env.prod`:
```bash
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@arryn.com
DJANGO_SUPERUSER_PASSWORD=[PASSWORD_SEGURO]
```

Crear superusuario automáticamente:
```bash
python manage.py createsuperuser --noinput
```

---

## 🚢 Paso 8: Despliegue en Producción

### 8.1 Actualizar docker-compose.prod.yml

```yaml
services:
  arryn-backend:
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_ENGINE=django.db.backends.postgresql
      - DATABASE_NAME=arryn_db
      - DATABASE_USER=arryn_admin
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_HOST=arryn-backend-db.xxxxxxxxx.us-east-1.rds.amazonaws.com
      - DATABASE_PORT=5432
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
```

### 8.2 Ejecutar en Servidor

```bash
# Copiar .env.prod
cp .env.prod .env

# Construir y ejecutar
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f arryn-backend
```

---

## 🔍 Paso 9: Monitoreo y Validación

### 9.1 Verificar Estado de la Aplicación

```bash
# Verificar que el contenedor esté corriendo
docker ps

# Verificar logs
docker logs arryn-backend

# Probar endpoint
curl http://localhost:8000/api/health
```

### 9.2 Verificar Conexión desde Admin Panel

1. Acceder a: `http://tu-servidor:8000/admin/`
2. Login con el superusuario creado
3. Verificar que puedes ver usuarios y grupos

### 9.3 Monitoreo en AWS

- **CloudWatch Metrics**: CPU, memoria, conexiones activas
- **RDS Events**: Ver eventos importantes
- **Performance Insights**: Analizar queries lentas (si está habilitado)

---

## 📊 Paso 10: Respaldo y Mantenimiento

### 10.1 Configurar Backups Automatizados

En **RDS Console** → **Modify**:
- Backup retention period: **7 días** (mínimo)
- Backup window: Seleccionar horario de bajo tráfico

### 10.2 Snapshots Manuales

```bash
# Via AWS CLI
aws rds create-db-snapshot \
    --db-instance-identifier arryn-backend-db \
    --db-snapshot-identifier arryn-db-snapshot-$(date +%Y%m%d)
```

---

## ⚠️ Troubleshooting

### Problema 1: No se puede conectar a RDS

**Verificar:**
- ✅ Security Group permite conexiones en puerto 5432
- ✅ RDS tiene "Public accessibility" habilitado (para testing)
- ✅ Endpoint correcto en variables de entorno
- ✅ Credenciales correctas

```bash
# Test con telnet
telnet arryn-backend-db.xxxxxxxxx.us-east-1.rds.amazonaws.com 5432
```

### Problema 2: Error de autenticación

```
FATAL: password authentication failed for user "arryn_admin"
```

**Solución:**
- Verificar que el password en `.env` sea correcto
- No debe tener espacios o caracteres especiales sin escapar

### Problema 3: Timeout de conexión

```
could not connect to server: Connection timed out
```

**Solución:**
- Revisar Security Group
- Verificar que el servidor tenga acceso a internet
- Verificar VPC routing tables

### Problema 4: Migraciones fallan

```
django.db.utils.OperationalError: FATAL: database "arryn_db" does not exist
```

**Solución:**
```bash
# Crear la base de datos manualmente
psql -h [ENDPOINT] -U arryn_admin -d postgres
CREATE DATABASE arryn_db;
\q
```

---

## 📋 Checklist Final

- [ ] Instancia RDS creada y en estado "Available"
- [ ] Security Group configurado correctamente
- [ ] Variables de entorno configuradas en `.env.prod`
- [ ] Conexión a RDS verificada exitosamente
- [ ] Migraciones aplicadas sin errores
- [ ] Tablas creadas en PostgreSQL
- [ ] Superusuario creado y puede acceder al admin panel
- [ ] Aplicación desplegada en servidor de producción
- [ ] Backups automatizados configurados
- [ ] Monitoreo CloudWatch activo
- [ ] Documentación de credenciales guardada de forma segura

---

## 🔗 Referencias Útiles

- [AWS RDS PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [Django Database Settings](https://docs.djangoproject.com/en/4.2/ref/settings/#databases)
- [Django Migrations](https://docs.djangoproject.com/en/4.2/topics/migrations/)

---

## 📞 Soporte

Para problemas o dudas:
- Revisar logs: `docker logs arryn-backend`
- Verificar AWS CloudWatch Logs
- Contactar al equipo de desarrollo

---

**Última actualización**: 5 de Octubre, 2025  
**Versión**: 1.0
