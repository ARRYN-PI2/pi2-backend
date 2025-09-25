import os
from django.conf import settings
from pymongo import MongoClient, ASCENDING
from bson import ObjectId  # para manejar los IDs de Mongo

try:
    # Configuration from environment variables
    MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
    mongo_port_str = os.getenv("MONGO_PORT", "27017").strip()
    MONGO_PORT = int(mongo_port_str if mongo_port_str else "27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "arryn_products_db")
    MONGO_TIMEOUT = int(os.getenv("MONGO_CONNECTION_TIMEOUT", 5000))
    MONGO_USER = os.getenv("MONGO_USER")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
    MONGO_AUTH_DB = os.getenv("MONGO_AUTH_DB", MONGO_DB_NAME)

    if MONGO_USER and MONGO_PASSWORD:
        mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_AUTH_DB}"
    else:
        mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=MONGO_TIMEOUT)
    # Test de conexión
    client.admin.command('ping')
    db = client[MONGO_DB_NAME]
    MONGO_AVAILABLE = True
    print(f"✅ MongoDB conectado: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}")
except Exception as e:
    print(f"⚠️  MongoDB no disponible: {e}")
    db = None
    MONGO_AVAILABLE = False

def obtener_por_categoria_ordenado(coleccion, categoria, limit=20):
    if not MONGO_AVAILABLE or db is None:
        return []
        
    collection = db[coleccion]
    cursor = (collection
              .find({"categoria": categoria}, {"_id": 1, "titulo": 1, "marca": 1, "precio_texto": 1,
                                               "precio_valor": 1, "moneda": 1, "categoria": 1,
                                               "imagen": 1, "link": 1, "fuente": 1, "fecha_extraccion": 1})
              .sort("precio_valor", ASCENDING)
              .limit(int(limit)))
    docs = list(cursor)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

def guardar_json(coleccion, data):
    if not MONGO_AVAILABLE or db is None:
        return ["mock_id_1", "mock_id_2"] if isinstance(data, list) else "mock_id_1"
        
    collection = db[coleccion]

    # Si es lista de JSONs
    if isinstance(data, list):
        result = collection.insert_many(data)
        return [str(_id) for _id in result.inserted_ids]

    # Si es un solo JSON
    result = collection.insert_one(data)
    return str(result.inserted_id)


def obtener_json(coleccion):
    if not MONGO_AVAILABLE or db is None:
        return []
        
    collection = db[coleccion]
    docs = list(collection.find({}))
    
    # Convertimos ObjectId a string
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def obtener_por_id(coleccion, id):
    if not MONGO_AVAILABLE or db is None:
        return None
        
    collection = db[coleccion]
    try:
        object_id = ObjectId(id)   # convertir string a ObjectId
    except Exception:
        return None
    doc = collection.find_one({"_id": object_id})
    if doc:
        doc["_id"] = str(doc["_id"])  # devolver como string para JSON
    return doc

def obtener_marcas(
    coleccion: str,
    with_counts: bool = False,
    fuente: str | None = None,
    categoria: str | None = None,
):
    """
    Retorna (brands:list[str], counts:dict[str,int]) usando agregación en Mongo.
    Normaliza marcas a MAYÚSCULAS + trim para evitar duplicados ("Nike", " NIKE ").
    Soporta filtros opcionales por fuente y categoría.
    """
    if not MONGO_AVAILABLE or db is None:
        # Datos de ejemplo cuando MongoDB no está disponible
        sample_brands = ["NIKE", "ADIDAS", "PUMA", "REEBOK"]
        if with_counts:
            sample_counts = {"NIKE": 10, "ADIDAS": 8, "PUMA": 5, "REEBOK": 3}
            return sample_brands, sample_counts
        return sample_brands, {}
    
    col = db[coleccion]

    match: dict = {"marca": {"$type": "string", "$ne": ""}}
    if fuente:
        match["fuente"] = fuente
    if categoria:
        match["categoria"] = categoria

    if with_counts:
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": {"$trim": {"input": {"$toUpper": "$marca"}}},
                "count": {"$sum": 1}
            }},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"_id": 1}}
        ]
        data = list(col.aggregate(pipeline))
        brands = [d["_id"] for d in data]
        counts = {d["_id"]: d["count"] for d in data}
        return brands, counts

    # Solo distintas sin conteo
    pipeline = [
        {"$match": match},
        {"$group": {"_id": {"$trim": {"input": {"$toUpper": "$marca"}}}}},
        {"$match": {"_id": {"$ne": None, "$ne": ""}}},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "marca": "$_id"}}
    ]
    data = list(col.aggregate(pipeline))
    brands = [d["marca"] for d in data]
    return brands, {}