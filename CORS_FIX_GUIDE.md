# 🔧 SOLUCIÓN AL PROBLEMA DE CORS - ARRYN BACKEND

## 📊 Diagnóstico Completado

### ✅ Información de AWS Encontrada

**Frontend (CloudFront + S3):**
- CloudFront URL: `https://d2objaapejmkqm.cloudfront.net`
- Dominio Principal: `https://arryn.app`
- Dominio Alternativo: `https://www.arryn.app`
- Bucket S3: `arryn-frontend-bucket`
- ✅ CloudFront está funcionando correctamente (HTTP 200)
- ✅ Bucket S3 tiene política pública configurada

**Backend (EC2):**
- IP: `3.133.11.109`
- Puerto: `8000`
- ✅ Backend está respondiendo

### 🔍 Problema Identificado

El error `AccessDenied` de AWS que estás viendo **NO es del S3/CloudFront**, sino un **problema de CORS** del backend.

**Causa:** El archivo `.env.prod` en el servidor EC2 tiene URLs de ejemplo en lugar de las URLs reales del frontend.

## 🛠️ Soluciones (Elige una)

### Opción 1: Despliegue Automático con Script (RECOMENDADO)

Si tienes la llave SSH de EC2:

```bash
cd /Users/esedesofiaaa/Documents/UPB\ TRABAJOS/ARRYN-PI2/Repositorios/pi2-backend

# Si tu llave SSH está en una ubicación personalizada:
export SSH_KEY_PATH="/ruta/a/tu/llave.pem"

# Ejecutar el script
./scripts/deploy_cors_fix.sh
```

### Opción 2: Despliegue Manual vía SSH

1. **Conéctate a tu servidor EC2:**
   ```bash
   ssh -i /ruta/a/tu/llave.pem ec2-user@3.133.11.109
   ```

2. **Navega al directorio del proyecto:**
   ```bash
   cd /home/ec2-user/arryn-backend
   # o
   cd ~/arryn-backend
   ```

3. **Edita el archivo .env.prod:**
   ```bash
   nano .env.prod
   ```

4. **Cambia la línea de CORS_ALLOWED_ORIGINS a:**
   ```bash
   CORS_ALLOWED_ORIGINS=https://arryn.app,https://www.arryn.app,https://d2objaapejmkqm.cloudfront.net
   ```

5. **Guarda (Ctrl+O, Enter, Ctrl+X) y reinicia los servicios:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

6. **Verifica los logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f arryn-backend
   ```

### Opción 3: Despliegue vía GitHub Actions

Si tienes CI/CD configurado:

1. **Haz commit de los cambios:**
   ```bash
   cd /Users/esedesofiaaa/Documents/UPB\ TRABAJOS/ARRYN-PI2/Repositorios/pi2-backend
   git add .env.prod
   git commit -m "fix: actualizar CORS_ALLOWED_ORIGINS con URLs reales de CloudFront"
   git push origin main
   ```

2. **Espera a que GitHub Actions despliegue automáticamente**

⚠️ **NOTA:** Si `.env.prod` está en `.gitignore` (debería estarlo), entonces necesitas actualizar las variables de entorno en GitHub Secrets o directamente en el servidor.

## 📝 Cambios Realizados Localmente

Los siguientes archivos han sido actualizados:

### 1. `.env.prod`
```bash
CORS_ALLOWED_ORIGINS=https://arryn.app,https://www.arryn.app,https://d2objaapejmkqm.cloudfront.net,http://localhost:5173
```

### 2. `Arryn_Back/infrastructure/config/settings.py`
Ya tiene la configuración correcta de CORS con:
- Headers permitidos
- Métodos permitidos
- Credentials habilitados

## 🔍 Verificación Post-Despliegue

### 1. Probar CORS desde el navegador:

Abre la consola del navegador (F12) en https://arryn.app y ejecuta:

```javascript
fetch('http://3.133.11.109:8000/api/products/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
})
  .then(response => response.json())
  .then(data => console.log('✅ CORS funciona:', data))
  .catch(error => console.error('❌ Error CORS:', error));
```

### 2. Probar desde la terminal:

```bash
curl -I -X OPTIONS http://3.133.11.109:8000/api/products/ \
  -H "Origin: https://arryn.app" \
  -H "Access-Control-Request-Method: GET"
```

Deberías ver headers como:
```
Access-Control-Allow-Origin: https://arryn.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: ...
```

## 🚨 Si el Problema Persiste

### Checklist de Troubleshooting:

1. **Backend no tiene las variables actualizadas:**
   - ✅ Verifica que el archivo `.env.prod` en EC2 tenga las URLs correctas
   - ✅ Reinicia los contenedores Docker después de cualquier cambio

2. **Frontend usa HTTP en lugar de HTTPS:**
   - ⚠️ Asegúrate de que tu frontend use `https://` para las peticiones al backend
   - ⚠️ O agrega `http://3.133.11.109:8000` a CORS_ALLOWED_ORIGINS

3. **Certificado SSL en CloudFront:**
   - ✅ Verifica que CloudFront tenga un certificado SSL válido
   - ✅ Revisa en AWS Console → CloudFront → tu distribución → General

4. **Security Groups de EC2:**
   - ✅ Verifica que el Security Group permita tráfico en el puerto 8000 desde cualquier IP (0.0.0.0/0)
   - AWS Console → EC2 → Security Groups

5. **El error real NO es de S3:**
   - Si el error dice "AccessDenied" pero viene de S3, verifica que no estés intentando acceder a archivos que no existen
   - Verifica las rutas en tu código frontend

## 📞 Necesitas la Llave SSH?

Si no encuentras la llave SSH para conectarte a EC2:

1. **Descárgala desde AWS Console:**
   - AWS Console → EC2 → Key Pairs
   - Si la perdiste, necesitarás crear una nueva

2. **O usa AWS Systems Manager (Session Manager):**
   - AWS Console → Systems Manager → Session Manager
   - Start Session → Selecciona tu instancia EC2

## 🔐 Configuración de GitHub Secrets (Opcional)

Si quieres que GitHub Actions despliegue automáticamente:

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Agrega estos secrets:
   - `SSH_PRIVATE_KEY`: Tu llave privada de EC2
   - `EC2_HOST`: 3.133.11.109
   - `EC2_USER`: ec2-user

---

**Archivo generado automáticamente con AWS CLI** 🤖
