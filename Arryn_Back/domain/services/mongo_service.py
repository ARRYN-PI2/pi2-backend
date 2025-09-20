from django.conf import settings
from pymongo import MongoClient
from bson import ObjectId  # para manejar los IDs de Mongo

client = MongoClient("mongodb://localhost:27017/")
db = client["mi_base_mongo"]

def guardar_json(coleccion, data):
    collection = db[coleccion]

    # Si es lista de JSONs
    if isinstance(data, list):
        result = collection.insert_many(data)
        return [str(_id) for _id in result.inserted_ids]

    # Si es un solo JSON
    result = collection.insert_one(data)
    return str(result.inserted_id)


def obtener_json(coleccion):
    collection = db[coleccion]
    docs = list(collection.find({}))
    
    # Convertimos ObjectId a string
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def obtener_por_id(coleccion, id):
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
    Normaliza marcas a MAYÚSCULAS + trim para evitar duplicados (“Nike”, “ NIKE ”).
    Soporta filtros opcionales por fuente y categoría.
    """
    col = db[coleccion]

    match = {"marca": {"$type": "string", "$ne": ""}}
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