import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializer import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from ...domain.services.mongo_service import guardar_json, obtener_json, obtener_por_id, obtener_marcas
from ...domain.services.parse_details import parse_details
from bson import ObjectId
from ...domain.services.mongo_service import db
from pymongo import ASCENDING


class ArchivosJsonView(APIView):
    def post(self, request):
        try:
            raw_body = request.body.decode("utf-8").strip()

            # Si viene como un JSON normal (objeto o lista)
            try:
                data = json.loads(raw_body)
                docs = data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                # Si falla, asumimos que son múltiples JSONs separados por saltos de línea
                docs = [json.loads(line) for line in raw_body.splitlines() if line.strip()]

            ids = guardar_json("archivos", docs)
            return Response(
                {"mensaje": "Guardado en Mongo", "ids": ids},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        docs = obtener_json("archivos")
        return Response(docs, status=status.HTTP_200_OK)
    
    
@api_view(['GET'])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(UserSerializer({'username': 'Juan', 'email':'juanmonsalve.23@hotmail.com' }).data)


@api_view(["POST"])
def createUser(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {"message": "Usuario creado correctamente", "id": user.id, "username": user.username},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET', 'PUT', 'DELETE'])
def userDetail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class DetallesAdicionalesView(APIView):
    def get(self, request):
        docs = obtener_json("archivos")

        resultados = []
        for doc in docs:
            if "detalles_adicionales" in doc:
                detalles_json = parse_details(doc["detalles_adicionales"])
                resultados.append({
                    "titulo": doc.get("titulo", "Sin título"),
                    "detalles_adicionales": detalles_json
                })

        return Response(resultados, status=status.HTTP_200_OK)
    

class DetallesPorIdView(APIView):
    def get(self, request, id):
        collection = db["archivos"]
        doc = collection.find_one({"_id": ObjectId(id)}, {"_id": 0})

        if not doc or "detalles_adicionales" not in doc:
            return Response({"error": "No se encontraron detalles adicionales"}, status=status.HTTP_404_NOT_FOUND)

        # Parsear los detalles como antes
        detalles_json = parse_details(doc["detalles_adicionales"])

        # Convertimos cada key:value en párrafos separados
        partes = []
        for k, v in detalles_json.items():
            if k.strip():  # si la clave no está vacía
                partes.append(f"{k}: {v}")
            else:  # si la clave está vacía, solo agregamos el valor
                partes.append(v)

        # Unir con saltos de línea dobles para formar párrafos
        detalles_final = "\n\n".join(partes)

        return Response({"detalles_adicionales": detalles_final}, status=status.HTTP_200_OK)
    
class BrandListView(APIView):


    def get(self, request):
        with_counts = str(request.query_params.get("with_counts", "false")).lower() in {"1","true","yes","y"}
        fuente = request.query_params.get("fuente")
        categoria = request.query_params.get("categoria")

        try:
            brands, counts = obtener_marcas(
                coleccion="archivos",
                with_counts=with_counts,
                fuente=fuente,
                categoria=categoria
            )
        except Exception as e:
            return Response({"detail": f"Error consultando Mongo: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = {"count": len(brands), "brands": brands}
        if with_counts:
            payload["counts"] = counts
        return Response(payload, status=status.HTTP_200_OK)


class OffersByCategoryView(APIView):
    """
    GET /offers/<category>/?limit=20
    Devuelve productos de la colección 'archivos' filtrados por categoría,
    ordenados por precio_valor ascendente.
    """
    DEFAULT_COLLECTION = "archivos"
    DEFAULT_LIMIT = 20

    def get(self, request, category: str):
        limit = request.query_params.get("limit", self.DEFAULT_LIMIT)

        try:
            limit = max(1, min(int(limit), 100))  # entre 1 y 100
        except ValueError:
            return Response({"error": "Parametro 'limit' inválido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            collection = db[self.DEFAULT_COLLECTION]
            cursor = (collection
                      .find({"categoria": category}, {
                          "_id": 1,
                          "titulo": 1,
                          "marca": 1,
                          "precio_texto": 1,
                          "precio_valor": 1,
                          "moneda": 1,
                          "categoria": 1,
                          "imagen": 1,
                          "link": 1,
                          "fuente": 1,
                          "fecha_extraccion": 1
                      })
                      .sort("precio_valor", ASCENDING)
                      .limit(limit))

            docs = list(cursor)
            for d in docs:
                d["_id"] = str(d["_id"])

            return Response({
                "category": category,
                "count": len(docs),
                "results": docs
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Error consultando Mongo: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
