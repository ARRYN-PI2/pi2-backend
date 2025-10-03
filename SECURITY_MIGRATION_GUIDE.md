# Guía de Migración: SECRET_KEY Seguro

## 📋 Resumen de Cambios

Este documento explica los cambios implementados para mejorar la seguridad del `SECRET_KEY` de Django según las mejores prácticas.

## ⚠️ Cambio Importante

**ANTES:** El `SECRET_KEY` tenía un valor por defecto hardcodeado en `settings.py`:
```python
SECRET_KEY = os.getenv("SECRET_KEY", 'django-insecure-default-key-change-in-production')
```

**AHORA:** El `SECRET_KEY` es obligatorio y debe provenir de una variable de entorno:
```python
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. ...")
```

## 🚀 Qué Hacer Como Desarrollador

### 1. Para Desarrollo Local

Si tu entorno ya tiene un archivo `.env.dev`, no necesitas hacer nada. El archivo ya fue actualizado con una clave segura de desarrollo.

Si tienes tu propio archivo `.env` personalizado, asegúrate de que tenga un `SECRET_KEY`:

```bash
# Generar una nueva clave
python scripts/generate_secret_key.py

# Agregar a tu .env
SECRET_KEY=la-clave-generada-por-el-script
```

### 2. Para Entornos de Staging/Producción

**IMPORTANTE:** Debes generar una nueva `SECRET_KEY` única para cada entorno:

```bash
# Generar clave
python scripts/generate_secret_key.py

# Configurar como variable de entorno
export SECRET_KEY="tu-clave-generada"

# O usar gestor de secretos (recomendado para producción)
# - AWS Secrets Manager
# - Azure Key Vault
# - Docker Secrets
# - GitHub Secrets (para CI/CD)
```

### 3. Si Usas Docker

El docker-entrypoint.sh ya está configurado para leer la variable `SECRET_KEY` del entorno. Solo asegúrate de que esté definida en tu archivo `.env.prod` o como variable de entorno del contenedor.

## 📝 Archivos Modificados

1. **`Arryn_Back/infrastructure/config/settings.py`**
   - Eliminado valor por defecto del SECRET_KEY
   - Agregada validación que lanza error si no está configurado

2. **`.env.example`**
   - Actualizado con instrucciones claras para generar SECRET_KEY

3. **`.env.dev`**
   - Incluye un SECRET_KEY seguro para desarrollo

4. **`.env.prod`**
   - SECRET_KEY vacío con instrucciones (debe ser configurado en producción)

5. **`README.md`**
   - Nueva sección de seguridad
   - Instrucciones para generar SECRET_KEY
   - Checklist de seguridad para despliegue

6. **`scripts/generate_secret_key.py`** (NUEVO)
   - Script utilitario para generar claves seguras

## 🔒 Mejores Prácticas

✅ **SÍ hacer:**
- Generar una clave única para cada entorno (dev, staging, prod)
- Usar gestores de secretos en producción (AWS Secrets Manager, Azure Key Vault)
- Rotar la SECRET_KEY periódicamente
- Mantener el SECRET_KEY fuera del control de versiones

❌ **NO hacer:**
- Compartir la misma SECRET_KEY entre entornos
- Commitear el SECRET_KEY real al repositorio
- Usar claves débiles o predecibles
- Compartir el SECRET_KEY por email o chat

## 🧪 Verificación

Puedes verificar que todo funciona correctamente:

```bash
# Verificar que Django requiere SECRET_KEY
unset SECRET_KEY
export DEBUG=True
python manage.py check
# Debería fallar con un mensaje claro

# Verificar con SECRET_KEY configurada
export SECRET_KEY="test-key"
python manage.py check
# Debería pasar exitosamente
```

## 📚 Recursos Adicionales

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Django Security Settings](https://docs.djangoproject.com/en/5.2/topics/security/)
- [OWASP Secret Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## ❓ Preguntas Frecuentes

### ¿Por qué este cambio?

Tener un SECRET_KEY hardcodeado en el código fuente es una vulnerabilidad de seguridad. Si el repositorio es público o si alguien obtiene acceso al código, podría usar esa clave para:
- Firmar cookies falsas
- Crear tokens de sesión válidos
- Comprometer la seguridad de la aplicación

### ¿Qué pasa con la clave anterior?

La clave anterior (`'django-insecure-default-key-change-in-production'`) debe ser considerada comprometida y no debe usarse en ningún entorno.

### ¿Necesito cambiar algo si solo desarrollo localmente?

No, el archivo `.env.dev` ya tiene una clave segura de desarrollo. Si usas ese archivo, no necesitas hacer ningún cambio.

### ¿Qué pasa si la aplicación falla al iniciar?

Si ves un error como "SECRET_KEY environment variable is not set", significa que necesitas configurar la variable de entorno. Sigue las instrucciones en la sección "Qué Hacer Como Desarrollador".

## 📞 Soporte

Si tienes problemas con estos cambios, por favor:
1. Revisa esta guía completa
2. Consulta el README.md actualizado
3. Ejecuta el script de generación: `python scripts/generate_secret_key.py`
4. Si el problema persiste, abre un issue en GitHub

---

**Fecha de implementación:** 2025-10-03
**Versión:** 1.0.0
