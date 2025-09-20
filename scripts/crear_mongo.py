from pymongo import MongoClient
from datetime import datetime

# Conectar al servidor MongoDB (localhost:27017 por defecto)
client = MongoClient("mongodb://localhost:27017/")

# Crear/usar la base de datos
db = client["mi_db_mongo"]

# Crear/usar la colección
coleccion = db["archivos"]

# Insertar documento de prueba
doc = {
    "nombre": "documento1.json",
    "contenido": {"clave": "valor", "lista": [1, 2, 3]},
    "creado_en": datetime.now()
}

resultado = coleccion.insert_one(doc)

print("Base de datos y colección creadas correctamente ✅")
print(f"ID insertado: {resultado.inserted_id}")
