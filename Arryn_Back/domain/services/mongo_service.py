from django.conf import settings
from pymongo import MongoClient

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
    docs = list(collection.find({}, {"_id": 0}))  # Ocultamos el _id de Mongo
    return docs