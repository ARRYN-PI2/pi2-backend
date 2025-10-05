#!/usr/bin/env python
"""
Script de validación de conexión a AWS RDS PostgreSQL
Uso: python scripts/validate_rds_connection.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    import psycopg2
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Error: Falta instalar dependencias: {e}")
    print("Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

# Cargar variables de entorno
env_file = BASE_DIR / '.env.prod'
if not env_file.exists():
    env_file = BASE_DIR / '.env.dev'
    
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Cargando configuración desde: {env_file}")
else:
    print("⚠️  No se encontró archivo .env, usando variables de entorno del sistema")

# Obtener credenciales
DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', 'localhost'),
    'port': int(os.getenv('DATABASE_PORT', 5432)),
    'database': os.getenv('DATABASE_NAME', 'postgres'),
    'user': os.getenv('DATABASE_USER', 'postgres'),
    'password': os.getenv('DATABASE_PASSWORD', ''),
}

def validate_config():
    """Validar que todas las variables estén configuradas"""
    print("\n" + "="*60)
    print("📋 VALIDACIÓN DE CONFIGURACIÓN")
    print("="*60)
    
    required_vars = ['DATABASE_HOST', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: NO CONFIGURADO")
        else:
            # Ocultar password
            display_value = '***' if 'PASSWORD' in var else value
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n❌ Variables faltantes: {', '.join(missing_vars)}")
        return False
    
    return True

def test_connection():
    """Probar conexión a PostgreSQL"""
    print("\n" + "="*60)
    print("🔌 PRUEBA DE CONEXIÓN A RDS")
    print("="*60)
    
    print(f"\nIntentando conectar a:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Port: {DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  User: {DB_CONFIG['user']}")
    
    try:
        print("\n⏳ Conectando... (timeout: 10 segundos)")
        conn = psycopg2.connect(
            **DB_CONFIG,
            connect_timeout=10
        )
        
        print("✅ Conexión exitosa!")
        
        # Obtener versión de PostgreSQL
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n📊 Versión PostgreSQL:")
        print(f"  {version.split(',')[0]}")
        
        # Verificar si hay tablas
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"\n📦 Tablas en la base de datos: {table_count}")
        
        if table_count > 0:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                LIMIT 10
            """)
            tables = cursor.fetchall()
            print("\n📋 Tablas encontradas:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("⚠️  No hay tablas creadas. Ejecuta: python manage.py migrate")
        
        # Verificar migraciones de Django
        try:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
            print(f"\n🔄 Migraciones aplicadas: {migration_count}")
        except psycopg2.errors.UndefinedTable:
            print("\n⚠️  Tabla django_migrations no existe. Ejecuta: python manage.py migrate")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Error de conexión:")
        print(f"  {str(e)}")
        print("\n🔧 Posibles soluciones:")
        print("  1. Verificar que el Security Group permita conexiones en puerto 5432")
        print("  2. Verificar que el endpoint sea correcto")
        print("  3. Verificar que las credenciales sean correctas")
        print("  4. Verificar que RDS tenga 'Public accessibility' habilitado (para testing)")
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        return False

def check_django_settings():
    """Verificar configuración de Django"""
    print("\n" + "="*60)
    print("⚙️  VALIDACIÓN DE DJANGO SETTINGS")
    print("="*60)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Arryn_Back.infrastructure.config.settings')
        import django
        django.setup()
        
        from django.conf import settings
        
        # Verificar configuración de base de datos
        db_config = settings.DATABASES['default']
        print(f"\n✅ Django settings cargados correctamente")
        print(f"  Engine: {db_config['ENGINE']}")
        print(f"  Name: {db_config['NAME']}")
        print(f"  Host: {db_config['HOST']}")
        print(f"  Port: {db_config['PORT']}")
        
        # Verificar SECRET_KEY
        if settings.SECRET_KEY:
            print(f"\n✅ SECRET_KEY configurado")
        else:
            print(f"\n❌ SECRET_KEY no configurado")
        
        # Verificar DEBUG
        print(f"\n📝 DEBUG mode: {settings.DEBUG}")
        if not settings.DEBUG:
            print("  ✅ Producción mode activado")
        else:
            print("  ⚠️  Development mode (cambiar a False en producción)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al cargar Django settings: {str(e)}")
        return False

def main():
    """Ejecutar todas las validaciones"""
    print("\n" + "="*60)
    print("🚀 VALIDADOR DE CONEXIÓN AWS RDS POSTGRESQL")
    print("="*60)
    
    results = {
        'config': validate_config(),
        'connection': False,
        'django': False
    }
    
    if results['config']:
        results['connection'] = test_connection()
        results['django'] = check_django_settings()
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("="*60)
    
    status_icon = lambda x: "✅" if x else "❌"
    
    print(f"\n{status_icon(results['config'])} Configuración de variables de entorno")
    print(f"{status_icon(results['connection'])} Conexión a PostgreSQL RDS")
    print(f"{status_icon(results['django'])} Configuración de Django")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "="*60)
        print("🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("="*60)
        print("\n✅ El sistema está listo para ejecutar migraciones:")
        print("   python manage.py migrate")
        print("\n✅ Y crear el superusuario:")
        print("   python manage.py createsuperuser")
        return 0
    else:
        print("\n" + "="*60)
        print("⚠️  ALGUNAS VALIDACIONES FALLARON")
        print("="*60)
        print("\n🔧 Revisa los errores anteriores y corrígelos antes de continuar.")
        print("📖 Consulta: AWS_RDS_DEPLOYMENT_GUIDE.md")
        return 1

if __name__ == '__main__':
    sys.exit(main())
